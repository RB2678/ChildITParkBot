import logging
from states.states import BotStates
from utils import safe_send

def register_teacher_handlers(bot, db, crm):
    # ----- Регистрация -----
    # Обработка ФИО
    @bot.message_handler(state=BotStates.entering_teacher_name)
    def process_teacher_name(message):
        user_id = message.chat.id
        teacher_name = message.text.strip()

        safe_send(bot, user_id, "Проверяем ваши данные в базе ИТ-Парка...")

        try:
            found_teachers = crm.teachers(name=teacher_name)
        except Exception as e:
            safe_send(bot, user_id, "Произошла ошибка при связи с сервером. Попробуйте позже.")
            logging.error(f"Ошибка при поиске преподавателя в CRM: {e}")
            bot.delete_state(user_id, message.chat.id)
            return

        if not found_teachers:
            safe_send(bot, user_id, "❌ Не удалось найти информацию. Проверьте правильность ФИО и введите его заново:")
            return

        if len(found_teachers) > 1:
            safe_send(bot, user_id, "⚠️ Найдено несколько преподавателей. Пожалуйста, введите ФИО полностью:")
            return

        crm_teacher = found_teachers[0]
        crm_id = crm_teacher.get("id")

        db.update_user(user_id, name=teacher_name, crm_id=crm_id, is_verified=True)
        safe_send(bot, user_id, "✅ Вы найдены в базе. Авторизация успешна!")

        bot.delete_state(user_id, message.chat.id)