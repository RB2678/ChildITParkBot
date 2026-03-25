from telebot import types
from states.states import BotStates
from utils import safe_send, check_password

def register_base_handlers(bot, db, crm):
    @bot.message_handler(commands=['start'])
    def cmd_start(message):
        user_id = message.chat.id
        # Очистка состояния при старте
        bot.delete_state(user_id, message.chat.id)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Родитель", "Ученик")

        safe_send(bot, user_id, "Добро пожаловать в детский ИТ-Парк! Выберите вашу роль:", reply_markup=markup)
        bot.set_state(user_id, BotStates.choosing_role, message.chat.id)

    @bot.message_handler(state=BotStates.choosing_role)
    def handle_role_choice(message):
        user_id = message.chat.id
        text = message.text.lower()

        # 1. Открытые роли
        if text == "родитель":
            db.update_user(user_id, role="parent")

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add("✅ Согласен", "❌ Не согласен")
            # ЗДЕСЬ НУЖНО ВСТАВИТЬ ССЫЛКУ НА ДОКУМЕНТ
            text = (
                "Для регистрации в базе ИТ-парка нам необходимо ваше согласие "
                "на обработку персональных данных (ФЗ-№152).\n\n"
                "Вы согласны продолжить?\n"
                "Текст соглашения: ссылка"
            )

            safe_send(bot, user_id, text, reply_markup=markup)
            bot.set_state(user_id, BotStates.accepting_privacy, message.chat.id)

        elif text == "ученик":
            db.update_user(user_id, role="student")
            safe_send(bot, user_id, "Привет, будущий айтишник! Введи свое имя:",
                      reply_markup=types.ReplyKeyboardRemove())
            # Здесь будет переход в состояние для ученика
            # bot.set_state(user_id, BotStates.entering_student_name, message.chat.id)

        # 2. Скрытые роли
        elif text in ["админ", "администратор", "admin"]:
            start_password_check(bot, db, message, "admin")

        elif text in ["преподаватель", "учитель", "teacher"]:
            start_password_check(bot, db, message, "teacher")

        else:
            safe_send(bot, user_id, "Пожалуйста, выберите роль кнопкой.")

    @bot.message_handler(state=BotStates.entering_password)
    def process_password(message):
        user_id = message.chat.id
        user_data = db.get_user(user_id)
        pending_role = user_data.get("pending_role")  # Берем роль, которую юзер хотел занять

        if check_password(pending_role, message.text):
            db.update_user(user_id, role=pending_role, pending_role=None)
            safe_send(bot, user_id, f"✅ Доступ разрешен. Роль {pending_role} активирована.")
            bot.delete_state(user_id, message.chat.id)
            # Здесь вызываем стартовое меню админа или учителя
        else:
            safe_send(bot, user_id, "❌ Неверный пароль. Попробуйте еще раз или выберите роль на кнопках:")
            # Можно вернуть его к выбору ролей
            cmd_start(message)


def start_password_check(bot, db, message, role):
    """Вспомогательная функция для запуска проверки пароля"""
    user_id = message.chat.id
    db.update_user(user_id, pending_role=role)  # Запоминаем, какой пароль ждем
    safe_send(bot, user_id, f"Введите пароль доступа для роли {role}:", reply_markup=types.ReplyKeyboardRemove())
    bot.set_state(user_id, BotStates.entering_password, message.chat.id)