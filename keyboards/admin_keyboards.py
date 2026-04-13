from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu_kb():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text="Запустить рассылку", callback_data="start_broadcast"),
        InlineKeyboardButton(text="Найти должников", callback_data="find_debtors")
    )
    return keyboard


def broadcast_roles_kb():
    keyboard = InlineKeyboardMarkup(row_width=1)
    roles = {
        "Администраторы": "admin",
        "Преподаватели": "teacher",
        "Родители": "parent",
        "Ученики": "student"
    }

    buttons = [
        InlineKeyboardButton(text=name, callback_data=cb)
        for name, cb in roles.items()
    ]
    buttons.append(InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_menu"))
    keyboard.add(*buttons)

    return keyboard

def broadcast_confirming_kb():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text="подтвердить", callback_data="confirm_broadcast"),
        InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_text")
    )

    return keyboard