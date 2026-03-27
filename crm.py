import time
import requests
import logging
import os
from config import CRM_HOSTNAME, CRM_EMAIL, CRM_API_TOKEN
logging.basicConfig(level=logging.INFO)

class AlfaCRMClient:
    def __init__(self, hostname, email, api_key, branch=3):
        self.hostname = hostname
        self.email = email
        self.api_key = api_key
        self.branch = branch

        self.token = None
        self.token_expires_at = 0

        # Справочники (name → id)
        self.groups = {}
        self.branches = {}
        self.users = {}
        self.subjects = {}

    # ---------- AUTH ----------

    def auth(self):
        logging.info("Авторизация в AlfaCRM")

        url = f"https://{self.hostname}/v2api/auth/login"
        resp = requests.post(url, json={
            "email": self.email,
            "api_key": self.api_key
        })

        try:
            resp.raise_for_status()
            data = resp.json()

            self.token = data["token"]
            self.token_expires_at = time.time() + 3600
        except requests.exceptions.HTTPError as e:
            logging.error(f"Ошибка при авторизации в AlfaCRM: {e}")

    def ensure_token(self):
        if not self.token or time.time() >= self.token_expires_at:
            self.auth()

    # ---------- BASE REQUEST ----------

    def request(self, method, path, params=None, payload=None):
        self.ensure_token()

        url = f"https://{self.hostname}{path}"
        headers = {
            "X-ALFACRM-TOKEN": self.token,
            "Accept": "application/json"
        }

        resp = requests.request(
            method,
            url,
            headers=headers,
            params=params,
            json=payload
        )

        if resp.status_code >= 400:
            raise RuntimeError(resp.text)

        return resp.json()

    # ---------- PAGINATION CORE ----------

    def list_all(self, path, filters=None, method="POST", page_size=50):
        filters = filters or {}
        page = 0
        all_items = []

        while True:
            payload = {
                "page": page,
                "count": page_size,
                **filters
            }

            data = self.request(
                method,
                f"/v2api/{self.branch}/{path}",
                payload=payload if method == "POST" else None,
                params=payload if method == "GET" else None,
            )

            items = data.get("items", [])
            all_items.extend(items)

            if len(items) < page_size:
                break

            page += 1

        return all_items

    # ---------- DICTIONARIES ----------

    def load_dictionaries(self):
        logging.info("Загрузка справочников")

        self.groups = {
            g["name"]: g["id"]
            for g in self.list_all("group/index", method="POST")
        }

        self.subjects = {
            s["name"]: s["id"]
            for s in self.list_all("subject/index", method="POST")
        }

        self.users = {
            u["name"]: u["id"]
            for u in self.list_all("user/index", method="POST")
        }

        self.branches = {
            b["name"]: b["id"]
            for b in self.list_all("branch/index", method="POST")
        }

    # ---------- FILTER MAPPING ----------

    def map_filters(self, raw_filters: dict) -> dict:
        """
        Преобразует человеко-читаемые фильтры в ID
        """
        mapped = {}

        for key, value in raw_filters.items():
            if key == "group":
                mapped["group_ids[]"] = self.groups[value]
            elif key == "branch":
                mapped["branch_ids[]"] = self.branches[value]
            elif key == "teacher":
                mapped["teacher_ids[]"] = self.users[value]
            elif key == "subject":
                mapped["subject_ids[]"] = self.subjects[value]
            else:
                mapped[key] = value

        return mapped

    # ---------- ENTITY HELPERS ----------

    def customers(self, **filters):
        return self.list_all(
            "customer/index",
            self.map_filters(filters)
        )

    def users_list(self, **filters):
        return self.list_all(
            "user/index",
            self.map_filters(filters)
        )

    def teachers(self, **filters):
        return self.list_all(
            "teacher/index",
            self.map_filters(filters)
        )

    def create_customer(self, student_name: str, parent_name: str, phone: str, legal_type: str):
        """ Создает нового клиента в AlfaCRM """
        self.ensure_token()

        # Маппинг типов лица из текстовых кнопок бота в ID API
        # 1 - физ. лицо, 2 - юр. лицо
        legal_type_id = 1 if "физическое" in legal_type.lower() else 2

        payload = {
            "name": student_name,           # В AlfaCRM это поле 'Имя ученика'
            "legal_name": parent_name,      # А это 'ФИО представителя'
            "phone": [phone],
            "legal_type": legal_type_id,    # Юридический статус
            "is_study": 0,                  # 0 - лид
            "branch_ids": [self.branch],    # ID филиала
            "lead_source_id": 23            # ID источника лида - телеграм-бот
        }

        path = f"/v2api/{self.branch}/customer/create"

        try:
            response = self.request("POST", path, payload=payload)

            if response and "model" in response:
                logging.info(f"Клиент {parent_name} успешно создан в CRM с ID {response['model'].get('id')}")
                return response["model"]
            else:
                logging.error(f"Ошибка структуры ответа CRM: {response}")
                return None

        except Exception as e:
            logging.error(f"Критическая ошибка при создании клиента: {e}")
            raise e