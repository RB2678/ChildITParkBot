import sqlite3
import json
from pathlib import Path
from config import DB_PATH

class Database:
    def __init__(self):
        self.path = Path(DB_PATH)
        self._init_db()

    def _get_connection(self):
        """Создает новое подключение к БД"""
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Создание таблиц, если они не существуют"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    role TEXT,
                    phone TEXT,
                    state TEXT,
                    crm_id INTEGER,
                    data TEXT       -- метаданные
                )
            """)
            # Таблицы для кэшей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS debtors_cache (
                    user_id TEXT PRIMARY KEY, 
                    data TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups_cache (
                    user_id TEXT PRIMARY KEY, 
                    data TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers_cache (
                    customer_id TEXT PRIMARY KEY,  
                    name TEXT,
                    data TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_students_cache (
                    group_id TEXT PRIMARY KEY,
                    students_json TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance_cache (
                    user_id TEXT PRIMARY KEY,
                    data TEXT
                )
            """)
            conn.commit()


    # --- Основные методы ---
    def get_user(self, user_id):
        """Возвращает данные пользователя, а если его нет в БД - то создает"""
        user_id = str(user_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),)).fetchone()

            if row:
                user_dict = dict(row)
                user_dict["data"] = json.loads(user_dict["data"]) if user_dict["data"] else {}
                return user_dict

            default_data = json.dumps({})
            cursor.execute(
                "INSERT INTO users (user_id, role, phone, state, data) VALUES (?, ?, ?, ?, ?)",
                (user_id, None, None, None, default_data)
            )
            conn.commit()
            return {"user_id": user_id, "role": None, "phone": None, "state": None, "crm_id": None, "data": default_data}


    def update_user(self, user_id, **kwargs):
        """Обновляет поля пользователя"""
        user_id = str(user_id)
        current_user = self.get_user(user_id)

        user_metadata = current_user.get("data")
        if not isinstance(user_metadata, dict):
            user_metadata = {}

        main_columns = ["role", "phone", "state", "crm_id"]

        # Списки для формирования динамического SQL
        set_parts = []
        params = []

        for key, value in kwargs.items():
            if key in main_columns:
                set_parts.append(f"{key} = ?")
                params.append(value)
            else:
                user_metadata[key] = value

        set_parts.append("data = ?")
        params.append(json.dumps(user_metadata, ensure_ascii=False))

        params.append(user_id)

        query = f"UPDATE users SET {', '.join(set_parts)} WHERE user_id = ?"

        with self._get_connection() as conn:
            conn.execute(query, params)
            conn.commit()


    def get_crm_id(self, user_id):
        """Возвращает id пользователя в AlfaCRM"""
        user_id = str(user_id)
        with self._get_connection() as conn:
            row = conn.execute("SELECT crm_id FROM users WHERE user_id = ?", (str(user_id),)).fetchone()
            return row["crm_id"] if row else None

    def get_users_by_role(self, role):
        """Возвращает список пользователей с заданной ролью"""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM users WHERE role = ?", (role,)).fetchall()
            result = {}
            for row in rows:
                d = dict(row)
                d["data"] = json.loads(d["data"]) if d["data"] else {}
                result[d["user_id"]] = d
            return result


    # --- Методы кэширования ---
    def save_debtors(self, user_id, debtors):
        """Сохраняет список должников в БД"""
        with self._get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO debtors_cache (user_id, data) VALUES (?, ?)",
                         (str(user_id), json.dumps(debtors, ensure_ascii=False))
            )
            conn.commit()


    def get_debtors(self, user_id):
        """Возвращает список должников из БД"""
        with self._get_connection() as conn:
            row = conn.execute("SELECT data FROM debtors_cache WHERE user_id = ?", (str(user_id),)).fetchone()
            return json.loads(row["data"]) if row else None


    def update_teachers_groups(self, user_id, groups):
        """Сохраняет список групп преподавателя в БД"""
        if groups is None: return
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO groups_cache (user_id, data) VALUES (?, ?)",
                (str(user_id), json.dumps(groups, ensure_ascii=False))
            )
            conn.commit()


    def get_teachers_groups(self, user_id):
        """Возвращает список групп преподавателя из БД"""
        with self._get_connection() as conn:
            row = conn.execute("SELECT data FROM groups_cache WHERE user_id = ?", (str(user_id),)).fetchone()
            return json.loads(row["data"]) if row else None

    def update_customers_cache(self, customers_list):
        """Сохраняет словарь клиентов {id: name} в БД"""
        if not customers_list: return

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for customer in customers_list:
                c_id = str(customer.get("id"))
                name = customer.get("name", "Неизвестно")
                data = json.dumps(customer, ensure_ascii=False)
                cursor.execute(
                    "INSERT OR REPLACE INTO customers_cache (customer_id, name, data) VALUES (?, ?, ?)",
                    (str(c_id), name, data)
                )
            conn.commit()

    def get_cached_customer_name(self, customer_id: int):
        """Возвращает имя клиента по ID из кэша"""
        with self._get_connection() as conn:
            row = conn.execute("SELECT name FROM customers_cache WHERE customer_id = ?", (str(customer_id),)).fetchone()
            return row["name"] if row else None


    def save_group_students(self, group_id, students):
        """
        Сохраняет список учеников конкретной группы
        :param group_id: ID группы из AlfaCRM
        :param students: список словарей [{id: int, name: str}]
        """
        if students is None: return

        group_id = str(group_id)
        students_json = json.dumps(students, ensure_ascii=False)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO groups_students_cache (group_id, students_json, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (group_id, students_json))
            conn.commit()


    def get_group_students(self, group_id):
        """Возвращает список ученик группы из кэша"""
        group_id = str(group_id)
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT students_json FROM groups_students_cache WHERE group_id = ?",
                (group_id,)
            ).fetchone()

            return json.loads(row["students_json"]) if row else None

    def clear_group_students_cache(self, group_id = None):
        """Очистка кэша для одной группы или для всех сразу"""
        with self._get_connection() as conn:
            if group_id:
                conn.execute("""DELETE FROM groups_students_cache WHERE group_id = ?""", (str(group_id),))
            else:
                conn.execute("DELETE FROM groups_students_cache")
            conn.commit()


    def get_attendance_cache(self, user_id):
        """Возвращает кэш посещаемости преподавателя"""
        user_id = str(user_id)
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT data FROM attendance_cache WHERE user_id = ?",
                (str(user_id),)
            ).fetchone()

            return json.loads(row["data"]) if row else None

    def save_attendance_cache(self, user_id, data):
        """Сохраняет кэш посещаемости"""
        if data is None: return

        user_id = str(user_id)
        data = json.dumps(data, ensure_ascii=False)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO attendance_cache (user_id, data) 
                VALUES (?, ?)
            """, (user_id, data))
            conn.commit()


    def clear_attendance_cache(self, user_id = None):
        """Очистка кэша посещаемости для одного преподавателя или для всех сразу"""
        with self._get_connection() as conn:
            if user_id:
                conn.execute("""DELETE FROM attendance_cache WHERE user_id = ?""", (str(user_id),))
            else:
                conn.execute("DELETE FROM attendance_cache")
            conn.commit()