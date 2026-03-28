from telebot import types
from states.states import BotStates
from utils import safe_send, get_contact_keyboard, format_phone

def register_parent_handlers(bot, db, crm):
    # ----- Регистрация -----
    # 1. Обработка согласия ПД
    @bot.message_handler(state=BotStates.accepting_privacy)
    def process_privacy(message):
        user_id = message.chat.id

        if "Согласен" in message.text and "Не" not in message.text:
            safe_send(bot, user_id, "Отлично! Введите ваше ФИО:",
                      reply_markup=types.ReplyKeyboardRemove())
            bot.set_state(user_id, BotStates.entering_parent_name, message.chat.id)
        elif "Не согласен" in message.text:
            safe_send(bot, user_id, "К сожалению, без согласия регистрация невозможна. /start")
            bot.delete_state(user_id, message.chat.id)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add("✅ Согласен", "❌ Не согласен")
            safe_send(bot, user_id, "Пожалуйста, используйте кнопки.", reply_markup=markup)

    # 2. Обработка ФИО родителя
    @bot.message_handler(state=BotStates.entering_parent_name)
    def process_full_name(message):
        user_id = message.chat.id
        db.update_user(user_id, full_name=message.text)
        safe_send(bot, user_id, "Введите ФИО ученика (ребенка):")
        bot.set_state(user_id, BotStates.entering_student_name, message.chat.id)

    # 3. Обработка ФИО ученика
    @bot.message_handler(state=BotStates.entering_student_name)
    def process_student_name(message):
        user_id = message.chat.id
        db.update_user(user_id, student_name=message.text)

        # Создание клавиатуры для выбора юридического статуса
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Физическое лицо", "Юридическое лицо")

        safe_send(bot, user_id, f"Принято! Теперь выберите ваш юридический статус:", reply_markup=markup)
        bot.set_state(user_id, BotStates.choosing_legal, message.chat.id)

    # 4. Обработка юридического статуса
    @bot.message_handler(state=BotStates.choosing_legal)
    def process_legal(message):
        user_id = message.chat.id
        legal_type = message.text

        if legal_type not in ["Физическое лицо", "Юридическое лицо"]:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add("Физическое лицо", "Юридическое лицо")
            safe_send(bot,
                      user_id,
                      "Пожалуйста, выберите один из вариантов на кнопках.",
                      reply_markup=markup
            )
            return

        db.update_user(user_id, legal_type=legal_type)

        # Запрос контакта (номера телефона)
        safe_send(bot,
                  user_id,
                  "Для завершения регистрации нам необходим ваш номер телефона. "
                  "Нажмите на кнопку ниже, чтобы отправить его.",
                  reply_markup=get_contact_keyboard())

        bot.set_state(user_id, BotStates.sending_phone, message.chat.id)

    # 5. Обработка полученного контакта
    @bot.message_handler(state=BotStates.sending_phone, content_types=['contact'])
    def process_contact(message):
        user_id = message.chat.id

        # Получаем номер (из контакта или текста, если ввели вручную)
        if message.contact:
            raw_phone = message.contact.phone_number
        else:
            raw_phone = message.text

        try:
            formatted = format_phone(raw_phone)
        except ValueError:
            safe_send(bot,
                      user_id,
                      "Ошибка в формате номера. Попробуйте еще раз или отправьте контакт кнопкой.",
                      reply_markup=get_contact_keyboard()
            )
            return

        safe_send(bot, user_id, "Проверяем ваши данные в базе ИТ-Парка...", reply_markup=types.ReplyKeyboardRemove())

        # Поиск в AlfaCRM (is_study=2 ищет по всем статусам)
        try:
            found_clients = crm.customers(phone=formatted, is_study=2)
        except Exception:
            safe_send(bot, user_id, "Произошла ошибка при связи с сервером. Попробуйте позже.")
            bot.delete_state(user_id, message.chat.id)
            return

        if found_clients:
            # 1. Клиент найден в базе
            crm_client = found_clients[0]
            crm_id = crm_client.get("id")

            db.update_user(user_id, phone=formatted, crm_id=crm_id, is_verified=True)
            safe_send(bot, user_id, f"✅ Вы найдены в базе. Авторизация успешна!")
        else:
            # 2. Клиента нет -> создается новый
            user_data = db.get_user(user_id)
            full_name = user_data.get("full_name", "Без имени")
            student_name = user_data.get("student_name", "Без имени")
            legal_type = user_data.get("legal_type", "Физическое лицо")

            new_customer = crm.create_customer(parent_name=full_name, student_name=student_name, phone=formatted, legal_type=legal_type)
            crm_id = new_customer.get("id")

            db.update_user(user_id, phone=formatted, crm_id=crm_id, is_verified=True)
            safe_send(bot, user_id, "🎉 Регистрация успешно завершена!")

        # Завершение цепочки состояний
        bot.delete_state(user_id, message.chat.id)