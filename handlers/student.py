import logging
from states.states import BotStates
from utils import safe_send


def register_student_handlers(bot, db, crm):
    # ----- Регистрация -----
    # 1. Обработка ФИО
    @bot.message_handler(state=BotStates.entering_name)
    def process_student_name(message):
        user_id = message.chat.id

        safe_send(bot, user_id, "Проверяем ваши данные в базе ИТ-Парка...")

        # Поиск в AlfaCRM (is_study=2 ищет по всем статусам)
        try:
            found_clients = crm.customers(name=message.text, is_study=2)
        except Exception as e:
            safe_send(bot, user_id, "Произошла ошибка при связи с сервером. Попробуйте позже.")
            logging.error(f"Ошибка при поиске ученика в CRM: {e}")
            bot.delete_state(user_id, message.chat.id)
            return

        if found_clients:
            # 1. Ученик найден в базе
            crm_client = found_clients[0]
            crm_id = crm_client.get("id")

            db.update_user(user_id, name=message.text, crm_id=crm_id, is_verified=True)
            safe_send(bot, user_id, "✅ Вы найдены в базе. Авторизация успешна!")
            bot.delete_state(user_id, message.chat.id)
        else:
            safe_send(bot,user_id,"❌ Не удалось найти информацию. Пожалуйста, проверьте правильность ввода данных" )