from states.states import BotStates
from utils import crm_registration

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