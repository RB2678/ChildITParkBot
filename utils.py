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