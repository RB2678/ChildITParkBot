import telebot
from telebot import custom_filters
from telebot.storage import StateMemoryStorage
import config
from storage import Database
from crm import AlfaCRMClient
from handlers.base import register_base_handlers
from handlers.parent import register_parent_handlers

# Инициализация базы и CRM
db = Database()
crm = AlfaCRMClient(
    hostname=config.CRM_HOSTNAME,
    email=config.CRM_EMAIL,
    api_key=config.CRM_API_TOKEN
)

# Инициализация бота с хранилищем состояний в памяти
state_storage = StatePickleStorage(file_path="./states/states.pkl")
bot = telebot.TeleBot(config.BOT_API_TOKEN, state_storage=state_storage)

# Регистрация функций в боте
register_base_handlers(bot, db, crm)
register_parent_handlers(bot, db, crm)
# Добавление фильтров для работы состояний
bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.TextMatchFilter())

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling(skip_pending=True)