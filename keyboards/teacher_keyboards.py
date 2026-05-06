from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def teacher_menu_kb():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text="Запустить рассылку по группам", callback_data="start_group_broadcast"),
        InlineKeyboardButton(text="Расписание занятий", callback_data="teachers_schedule"),
        InlineKeyboardButton(text="Отметить посещаемость", callback_data="mark_attendance" ),
        InlineKeyboardButton(text="Список групп", callback_data="teachers_groups_list")
    )
    return keyboard


def to_menu_kb():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text="В меню", callback_data="to_teacher_menu"))
    return keyboard


def schedule_kb(lessons, db):
    keyboard = InlineKeyboardMarkup(row_width=1)

    for lesson in lessons:
        time_from = lesson.get("time_from", '00:00')[11:16]
        time_to = lesson.get("time_to", '00:00')[11:16]

        lesson_name = None

        if lesson.get("lesson_type_id") == 1:
            pass
            # Получить имя ученика на индивидуальном занятии
        elif lesson.get("lesson_type_id") == 2:
            pass
            # Получить название группы или курса
        else:
            lesson_name = None

        text = f"{time_from} — {time_to} | {lesson_name}"
        lesson_id = lesson.get("id", None)
        keyboard.add(InlineKeyboardButton(text=text, callback_data=f"att_lesson_{lesson_id}"))

    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="to_teacher_menu"))
    return keyboard


def attendance_kb(students_dict):
    keyboard = InlineKeyboardMarkup(row_width=1)

    for cust_id, data in students_dict.items():
        status_emoji = "✅" if data.get("is_attend", False) else "❌"
        text = f"{status_emoji} {data.get('name')}"

        keyboard.add(InlineKeyboardButton(text=text, callback_data=f"att_toggle_{cust_id}"))

    keyboard.add(
        InlineKeyboardButton(text="Отправить в CRM", callback_data="att_submit"),
        InlineKeyboardButton(text="Назад", callback_data="to_schedule_kb")
    )
    return keyboard