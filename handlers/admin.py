from keyboards.admin_keyboards import admin_menu_kb, broadcast_roles_kb
from utils import safe_send


def register_admin_handlers(bot, db, crm):
    # ----- Админ-панель -----
    @bot.message_handler(commands=["admin"])
    def admin_start(message):
        user_id = message.from_user.id
        safe_send(bot, user_id, f"Добро пожаловать в панель управления", reply_markup=admin_menu_kb())

    @bot.callback_query_handler(func=lambda call: call.data == "start_broadcast")
    def start_broadcast(call):
        user_id = call.message.chat.id
        safe_send(bot, user_id, "Выберите для кого запустить рассылку:", reply_markup=broadcast_roles_kb())