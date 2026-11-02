from services import auth_service
from ui.common import ask, new_password, password


def login():
    username = ask("Логин")
    return auth_service.authenticate(username, password())


def register():
    print("Самостоятельная регистрация создаёт пользователя с ролью руководителя.")
    username = ask("Логин")
    full_name = ask("ФИО")
    user = auth_service.register(username, new_password(), full_name)
    print(f"Пользователь {user.username} зарегистрирован. Выполните вход.")


def change_password(actor_id):
    old_password = password("Текущий пароль")
    auth_service.change_password(actor_id, old_password, new_password())
    print("Пароль изменён.")
