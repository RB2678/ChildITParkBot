from telebot.handler_backends import State, StatesGroup

class BotStates(StatesGroup):
    # Состояния регистрации
    choosing_role = State()         # Выбор роли (админ/преподаватель/родитель)
    entering_password = State()     # Ввод пароля для спец. ролей

    # Состояния для родителя
    accepting_privacy = State()     # Согласие на обработку персональных данных
    entering_parent_name = State()  # Это пойдет в legal_name
    entering_student_name = State() # Это пойдет в name
    choosing_legal = State()        # Физ/Юр лицо
    sending_phone = State()         # Отправка контакта
    check_contract = State()        # Проверка наличия договора

    # Состояния для ученика
    entering_name = State()

    # Состояния для администраторов
    entering_admin_name = State()
    processing_broadcast = State()
    confirming_broadcast = State()
    broadcast_text = State()

    # Состояния для преподавателей
    entering_teacher_name = State()
    entering_lesson_note = State()

    # Состояния для CRM/Договоров
    waiting_contract = State()      # Ожидание подписания договора