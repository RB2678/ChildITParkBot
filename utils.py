import re
import hashlib
import logging
from telebot.apihelper import ApiTelegramException
from telebot import types
from config import ADMIN_PW_DIGEST, TEACHER_PW_DIGEST

def format_phone(phone: str) -> str:
    """Очищает и форматирует номер телефона в формат +7(XXX)XXX-XX-XX"""
    digits = re.sub(r"\D", "", phone)

    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits

    if len(digits) != 11 or not digits.startswith("7"):
        raise ValueError("Неверный формат номера")

    return f"+7({digits[1:4]}){digits[4:7]}-{digits[7:9]}-{digits[9:11]}"

def check_password(role: str, password: str) -> bool:
    """Проверяет хэш пароля в зависимости от роли"""
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()

    if role == "admin":
        return digest == ADMIN_PW_DIGEST
    elif role == "teacher":
        return digest == TEACHER_PW_DIGEST

    return False

def get_contact_keyboard() -> types.ReplyKeyboardMarkup:
    """Возвращает клавиатуру для запроса контакта"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    contact_button = types.KeyboardButton("Отправить номер телефона", request_contact=True)
    keyboard.add(contact_button)
    return keyboard

def safe_send(bot, chat_id, text, **kwargs):
    """Безопасная отправка сообщения с отловом ошибок API Telegram"""
    try:
        return bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except ApiTelegramException as e:
        logging.error(f"Ошибка Telegram API при отправке в чат {chat_id}: {e}")
    except Exception as e:
        logging.error(f"Неожиданная ошибка при отправке в чат {chat_id}: {e}")
    return None

def safe_delete(bot, chat_id, message_id):
    """Безопасное удаление сообщения (не роняет бота, если сообщение уже удалено пользователем)"""
    try:
        return bot.delete_message(chat_id=chat_id, message_id=message_id)
    except ApiTelegramException as e:
        logging.warning(f"Не удалось удалить сообщение {message_id} в чате {chat_id}: {e}")
    except Exception as e:
        logging.error(f"Неожиданная ошибка при удалении сообщения {message_id}: {e}")
    return None

def crm_registration(message, bot, db, crm, role_settings):
    """
    Общая логика регистрации для всех ролей.
    role_settings: dict с ключами 'method', 'params', 'label'
    """
    user_id = message.chat.id
    full_name = message.text.strip()

    # Базовая валидация
    if len(full_name.split()) < 2:
        safe_send(bot, user_id, "Введите ФИО полностью:")
        return

    safe_send(bot, user_id, f"Проверяем данные в базе...")

    try:
        # Вызов метода CRM (customers, teachers или users_list)
        search_func = getattr(crm, role_settings['method'])
        results = search_func(name=full_name, **role_settings.get('params', {}))
    except Exception as e:
        logging.error(f"CRM Error [{role_settings['method']}]: {e}")
        safe_send(bot, user_id, "Ошибка связи с сервером. Попробуйте позже.")
        bot.delete_state(user_id, message.chat.id)
        return

    if not results:
        safe_send(bot, user_id, f"❌ {role_settings['label']} не найден. Проверьте ФИО и введите заново:")
        return

    if len(results) > 1:
        safe_send(bot, user_id, "⚠️ Найдено несколько совпадений. Введите ФИО более точно:")
        return

    # Успешная регистрация
    crm_obj = results[0]
    db.update_user(user_id, name=full_name, crm_id=crm_obj.get("id"), is_verified=True)

    safe_send(bot, user_id, f"✅ Доступ разрешен. Роль: {role_settings['label']}.")
    bot.delete_state(user_id, message.chat.id)