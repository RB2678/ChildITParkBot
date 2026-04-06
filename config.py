import os
from dotenv import load_dotenv

load_dotenv(".env")

BOT_API_TOKEN = os.getenv("BOT_API_TOKEN")

CRM_API_TOKEN = os.getenv("CRM_API_TOKEN")
CRM_EMAIL = os.getenv("CRM_EMAIL")
CRM_HOSTNAME = os.getenv("CRM_HOSTNAME")

ADMIN_PW_DIGEST = os.getenv("ADMIN_PASSWORD")
TEACHER_PW_DIGEST = os.getenv("TEACHER_PASSWORD")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db.json")

PRIVACY_POLITIC_URL = os.getenv("PRIVACY_POLITIC_URL")