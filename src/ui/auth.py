from services import auth_service
from services.common import ServiceError
from ui.common import ask, ask_int, new_password, password


def login():
    username = ask("Логин")
    return auth_service.authenticate(username, password())


def register():
    roles = auth_service.REGISTRATION_ROLES
    print("Выберите роль нового пользователя:")
    for number, role_name in enumerate(roles, 1):
        print(f"{number}. {role_name}")
    print("0. Отмена")
    choice = ask_int("Номер роли")
    if choice == 0:
        return
    if not 1 <= choice <= len(roles):
        raise ServiceError("Такой роли нет в меню.")
    username = ask("Логин")
    full_name = ask("ФИО")
    user = auth_service.register(username, new_password(), full_name, roles[choice - 1])
    print(f"Пользователь {user.username} зарегистрирован. Роль: {user.role_name}. Выполните вход.")


def change_password(actor_id):
    old_password = password("Текущий пароль")
    auth_service.change_password(actor_id, old_password, new_password())
    print("Пароль изменён.")
