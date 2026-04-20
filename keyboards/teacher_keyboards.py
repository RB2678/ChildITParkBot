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