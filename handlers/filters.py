from telebot.custom_filters import AdvancedCustomFilter

class RoleFilter(AdvancedCustomFilter):
    key = 'role'

    def __init__(self, db):
        self.db = db

    def check(self, message, role):
        """
        message: объект сообщения
        role: значение, переданное в декоратор)
        """
        user_id = message.from_user.id
        user_data = self.db.get_user(user_id)

        # Если пользователя нет, назначаем метку
        if not user_data or not user_data.get('role'):
            user_role = "unregistered"
        else:
            user_role = user_data.get("role", "unregistered")

        if isinstance(role, list):
            return user_role in role

        return user_role == role