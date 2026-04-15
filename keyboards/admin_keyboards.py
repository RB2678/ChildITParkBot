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
        InlineKeyboardButton(text=name, callback_data="bc_role:" + cb)
        for name, cb in roles.items()
    ]
    buttons.append(InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_menu"))
    keyboard.add(*buttons)

    return keyboard


def broadcast_confirming_kb():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text="Подтвердить", callback_data="confirm_broadcast"),
        InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_text")
    )

    return keyboard


def to_menu_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text="В меню", callback_data="to_menu"))
    return kb


def debtors_pagination_kb(current_page: int, total_pages: int):
    keyboard = InlineKeyboardMarkup(row_width=2)

    if total_pages <= 1:
        keyboard.add(InlineKeyboardButton(text="В меню", callback_data="to_menu"))
        return keyboard

    if current_page == 0:
        keyboard.add(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"to_page_{current_page + 1}"))
    elif current_page + 1 == total_pages:
        keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"to_page_{current_page - 1}"))
    else:
        keyboard.add(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"to_page_{current_page - 1}"),
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"to_page_{current_page + 1}"),
        )

    keyboard.add(InlineKeyboardButton(text="В меню", callback_data="to_menu"))
    return keyboard