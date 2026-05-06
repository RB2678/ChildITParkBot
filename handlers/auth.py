import logging
from states.states import BotStates
from utils import safe_send
from handlers.admin import send_admin_menu
from handlers.teacher import send_teacher_menu

# Конфигурация специфики ролей
REG_CONFIG = {
    'student': {
        'method': 'customers',
        'params': {'is_study': 2},
        'label': 'Ученик'
    },
    'teacher': {
        'method': 'teachers',
        'params': {},
        'label': 'Преподаватель'
    },
    'admin': {
        'method': 'users_list',
        'params': {},
        'label': 'Администратор'
    }
}

def register_all_auth_handlers(bot, db, crm):
    @bot.message_handler(state=BotStates.entering_name)
    def student_reg(message):
        crm_registration(message, bot, db, crm, REG_CONFIG['student'])

    @bot.message_handler(state=BotStates.entering_teacher_name)
    def teacher_reg(message):
        crm_registration(message, bot, db, crm, REG_CONFIG['teacher'])

    @bot.message_handler(state=BotStates.entering_admin_name)
    def admin_reg(message):
        crm_registration(message, bot, db, crm, REG_CONFIG['admin'])

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
    crm_id = crm_obj.get("id")
    db.update_user(user_id, name=full_name, crm_id=crm_id, is_verified=True)

    safe_send(bot, user_id, f"✅ Доступ разрешен. Роль: {role_settings['label']}.")

    match role_settings['label']:
        case 'Администратор':
            send_admin_menu(bot, user_id)
        case 'Преподаватель':
            send_teacher_menu(bot, user_id)
            groups = crm.get_teachers_groups(crm_id)
            db.update_teachers_groups(user_id, groups)

            if groups:
                safe_send(bot, user_id, f"📚 Синхронизировано групп: {len(groups)}")
            else:
                safe_send(bot, user_id, "⚠️ У вас пока нет активных групп в системе.")


    bot.delete_state(user_id, message.chat.id)