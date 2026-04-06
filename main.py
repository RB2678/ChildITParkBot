import telebot
from telebot import custom_filters, StateMemoryStorage
# from telebot.storage import StatePickleStorage
import config
from storage import Database
from crm import AlfaCRMClient
from handlers.base import register_base_handlers
from handlers.parent import register_parent_handlers
from handlers.student import register_student_handlers
from handlers.admin import register_admin_handlers
from handlers.teacher import register_teacher_handlers
from handlers.auth import register_all_auth_handlers
from handlers.filters import RoleFilter

# Инициализация базы и CRM
db = Database()
crm = AlfaCRMClient(
    hostname=config.CRM_HOSTNAME,
    email=config.CRM_EMAIL,
    api_key=config.CRM_API_TOKEN
)

# Инициализация бота с хранилищем состояний в памяти
state_storage = StateMemoryStorage()
bot = telebot.TeleBot(config.BOT_API_TOKEN, state_storage=state_storage)

# Добавление фильтров для работы состояний
bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.TextMatchFilter())
bot.add_custom_filter(RoleFilter(db))

# Регистрация функций в боте
register_admin_handlers(bot, db, crm)
register_parent_handlers(bot, db, crm)
register_student_handlers(bot, db, crm)
register_teacher_handlers(bot, db, crm)
register_base_handlers(bot, db)
register_all_auth_handlers(bot, db, crm)

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling(skip_pending=True)