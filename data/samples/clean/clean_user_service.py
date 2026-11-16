class UserService:
    def __init__(self):
        self._users = {}

    def get_user(self, user_id: str):
        return self._users.get(user_id)

    def register_user(self, user_id: str, name: str):
        if not user_id or not name:
            raise ValueError('Invalid user parameters')
        self._users[user_id] = name
        return True
