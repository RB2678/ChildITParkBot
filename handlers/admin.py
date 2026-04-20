from keyboards.admin_keyboards import *
from utils import safe_send, safe_edit
from states.states import BotStates
from telebot import types

BROADCAST_ROLES = ['admin', 'student', 'parent', 'teacher']

def register_admin_handlers(bot, db, crm):
    # ----- Админ-панель -----
    @bot.message_handler(commands=["admin", "start"], role="admin")
    def admin_start_msg(message: types.Message):
        send_admin_menu(bot, message.chat.id)


    @bot.callback_query_handler(func=lambda call: call.data == "to_menu", role="admin")
    def admin_start_call(call: types.CallbackQuery):
        bot.answer_callback_query(call.id)
        send_admin_menu(bot, call.message.chat.id)


    # ----- Рассылка -----
    @bot.callback_query_handler(func=lambda call: call.data == "start_broadcast", role="admin")
    def start_broadcast(call):
        bot.answer_callback_query(call.id)
        user_id = call.message.chat.id
        safe_edit(bot=bot, chat_id=user_id, message_id=call.message.message_id,
                  text="Выберите для кого запустить рассылку:", reply_markup=broadcast_roles_kb()
        )
        bot.set_state(user_id, BotStates.broadcast_text, user_id)


    @bot.callback_query_handler(func=lambda call: call.data.startswith("bc_role:"), role="admin",
                                state=BotStates.broadcast_text)
    def choosing_roles_broadcast(call):
        bot.answer_callback_query(call.id)
        user_id = call.message.chat.id
        msg_id = call.message.message_id
        target_role = ""

        if call.data.startswith("bc_role:"):
            target_role = call.data.split(":")[1]
        else:
            with bot.retrieve_data(user_id, call.message.chat.id) as data:
                target_role = data.get("target_role")

        roles_map = {
            "admin": "Администратор",
            "parent": "Родитель",
            "student": "Ученик",
            "teacher": "Преподаватель"
        }

        safe_edit(
            bot=bot, chat_id=user_id, message_id=msg_id,
            text=f"Введите текст рассылки для роли {roles_map[target_role]}:",
            reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
                types.InlineKeyboardButton(text="Отмена", callback_data=f"cancel_broadcast")
            ),
        )

        bot.set_state(
            user_id,
            BotStates.processing_broadcast,
            call.message.chat.id
        )
        bot.add_data(user_id=user_id, chat_id=call.message.chat.id, target_role=target_role)


    @bot.callback_query_handler(func=lambda call: call.data.startswith("back_to_menu"), role="admin")
    def back_to_menu(call):
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id)
        bot.delete_state(user_id=chat_id, chat_id=chat_id)
        safe_edit(bot=bot, chat_id=chat_id, message_id=call.message.message_id,
                  text=f"Добро пожаловать в панель управления",
                  reply_markup=admin_menu_kb()
        )


    @bot.message_handler(content_types=["text"], role="admin", state=BotStates.processing_broadcast)
    def confirming_broadcast(message):
        user_id = message.chat.id
        text=message.text.strip()

        bot.add_data(user_id=user_id, chat_id=message.chat.id, broadcast_text=text)
        preview_text = "Так будет выглядеть сообщение:\n\n" + text

        safe_send(
            bot=bot,
            chat_id=user_id,
            text=preview_text,
            reply_markup=broadcast_confirming_kb()
        )
        bot.set_state(user_id, BotStates.confirming_broadcast, message.chat.id)


    @bot.callback_query_handler(func=lambda call: call.data == "confirm_broadcast", role="admin",
                                state=BotStates.confirming_broadcast)
    def processing_broadcast(call):
        admin_id = call.message.chat.id

        with bot.retrieve_data(admin_id, call.message.chat.id) as data:
            text = data.get("broadcast_text")
            target_role = data.get("target_role")

        users = db.get_users_by_role(target_role)

        for user in users:
            if user == admin_id:
                continue

            safe_send(bot, user, text)

        bot.answer_callback_query(call.id)
        bot.delete_state(admin_id, call.message.chat.id)
        safe_send(bot, admin_id, "Рассылка успешно завершена", reply_markup=to_menu_kb())


    @bot.callback_query_handler(func=lambda call: call.data == "back_to_text", role="admin")
    def back_to_text(call):
        chat_id=call.message.chat.id
        bot.set_state(chat_id, BotStates.broadcast_text, call.message.chat.id)
        choosing_roles_broadcast(call)
        bot.answer_callback_query(call.id)


    @bot.callback_query_handler(func=lambda call: call.data == "cancel_broadcast", role="admin")
    def cancel_broadcast(call):
        user_id = call.message.chat.id
        bot.delete_state(user_id, call.message.chat.id)
        safe_send(bot, user_id, "Рассылка отменена")
        send_admin_menu(bot, user_id)
        bot.answer_callback_query(call.id)


    # ----- Поиск должников -----
    @bot.callback_query_handler(func=lambda call: call.data == "find_debtors", role="admin")
    def find_debtors(call):
        bot.answer_callback_query(call.id)
        user_id = call.message.chat.id
        debtors=crm.customers(lesson_count_to=-1)

        if not debtors:
            safe_send(bot, user_id, "Должников не найдено", reply_markup=to_menu_kb())
            return

        db.save_debtors(user_id, debtors)

        text, total_pages = get_debtors_page_content(debtors)
        safe_send(bot, user_id, text, reply_markup=debtors_pagination_kb(0, total_pages))


    @bot.callback_query_handler(func=lambda call: call.data.startswith("to_page_"), role="admin")
    def change_page(call):
        bot.answer_callback_query(call.id)
        user_id = call.message.chat.id
        page = int(call.data.split("_")[2])
        debtors = db.get_debtors(user_id)

        if not debtors:
            return

        page_content, total_pages = get_debtors_page_content(debtors, page)

        safe_edit(bot=bot,
                  chat_id=user_id,
                  message_id=call.message.message_id,
                  text= page_content,
                  reply_markup=debtors_pagination_kb(current_page=page, total_pages=total_pages)
        )


    def get_debtors_page_content(debtors, page = 0, size = 5):
        """
        Вспомогательная функция для получения одной страницы должников
        text: содержимое заданной страницы
        total_pages: общее количество страниц
        """
        start = page * size
        end = start + size
        subset = debtors[start:end]
        total_pages = (len(debtors) + size - 1) // size

        if not subset:
            return "Данных больше нет", 0

        text = f"Список должников (стр. {page+1}/{total_pages}):\n\n"

        for debtor in subset:
            debt = str(debtor.get("balance")).strip('-')
            text += (f"Клиент: {debtor.get('legal_name')}\n"
                     f"Ученик: {debtor.get('name')}\n"
                     f"Задолженность: {debt}\n\n")

        return text, total_pages

def send_admin_menu(bot, user_id):
    safe_send(
        bot,
        user_id,
        f"Добро пожаловать в панель управления администратора",
        reply_markup=admin_menu_kb()
    )