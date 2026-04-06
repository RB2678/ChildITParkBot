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

        if not user_data:
            return False

        user_role = user_data.get('role')

        if isinstance(role, list):
            return user_role in role

        return user_role == role