import json
import logging
import shutil
from pathlib import Path
from config import DB_PATH

class Database:
    def __init__(self):
        self.path = Path(DB_PATH)
        self.bak_path = self.path.with_suffix(".json.bak")
        self.data = {"users": {}}
        self.load_db()

    def load_db(self):
        """Загрузка данных с проверкой бэкапа"""
        if self._try_load(self.path):
            return

        logging.warning(f"Основной файл {self.path.name} поврежден, пробуем бэкап...")
        if self._try_load(self.bak_path):
            logging.info("Данные восстановлены из .bak")
            return

        logging.error("Не удалось прочитать данные. Создаем пустую базу.")
        self.data = {"users": {}}
        self.save_db()

    def _try_load(self, path: Path) -> bool:
        if path.exists() and path.stat().st_size > 0:
            try:
                self.data = json.loads(path.read_text(encoding="utf-8"))
                return True
            except Exception as e:
                logging.error(f"Ошибка загрузки {path.name}: {e}")
        return False

    def save_db(self):
        """Атомарное сохранение (сначала в темп, потом замена)"""
        temp_path = self.path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)

            # Если основной файл есть, делаем его бэкапом
            if self.path.exists():
                shutil.copy2(self.path, self.bak_path)

            # Заменяем основной файл временным
            temp_path.replace(self.path)
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            logging.error(f"Ошибка сохранения БД: {e}")

    # --- Методы-помощники для удобства ---

    def get_user(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data["users"]:
            self.data["users"][user_id] = {
                "role": None,
                "phone": None,
                "state": None,
                "data": {}
            }
            self.save_db()
        return self.data["users"][user_id]

    def update_user(self, user_id, **kwargs):
        """Обновляет поля пользователя и сразу сохраняет"""
        user = self.get_user(user_id)
        user.update(kwargs)
        self.save_db()