from repositories.role_repository import RoleRepository
from repositories.user_repository import UserRepository
from services.auth_service import hash_password
from services.common import (
    ACCOUNTANT, MANAGER, ServiceError, require_user, required_text, session, valid_username,
)


def require_manager(conn, actor_id):
    if require_user(conn, actor_id).role_name != MANAGER:
        raise ServiceError("Управление пользователями доступно только руководителю.")


def current_user(actor_id):
    with session() as conn:
        return require_user(conn, actor_id)


def list_roles(actor_id):
    with session() as conn:
        require_manager(conn, actor_id)
        return RoleRepository(conn).get_all()


def list_users(actor_id):
    with session() as conn:
        require_manager(conn, actor_id)
        return UserRepository(conn).get_all()


def supported_role(conn, role_id):
    role = RoleRepository(conn).get_by_id(role_id)
    if role is None or role.role_name not in (ACCOUNTANT, MANAGER):
        raise ServiceError("Выберите роль бухгалтера или руководителя.")
    return role


def create_user(actor_id, username, password, full_name, role_id):
    username = valid_username(username)
    full_name = required_text(full_name, "ФИО")
    password_hash = hash_password(password)
    with session(write=True) as conn:
        require_manager(conn, actor_id)
        users = UserRepository(conn)
        supported_role(conn, role_id)
        if users.get_by_username(username):
            raise ServiceError("Пользователь с таким логином уже существует.")
        return users.create(username, password_hash, full_name, role_id)


def protect_last_active_role(users, target, keeps_role):
    if target.is_active and not keeps_role and users.count_active_by_role(target.role_name) <= 1:
        label = "бухгалтера" if target.role_name == ACCOUNTANT else "руководителя"
        raise ServiceError(f"Нельзя отключить, удалить или сменить роль последнего активного {label}.")


def update_user(actor_id, user_id, full_name, role_id, is_active):
    full_name = required_text(full_name, "ФИО")
    if is_active not in (0, 1):
        raise ServiceError("Активность должна быть 0 или 1.")
    with session(write=True) as conn:
        require_manager(conn, actor_id)
        users = UserRepository(conn)
        target = users.get_by_id(user_id)
        if target is None:
            raise ServiceError("Пользователь не найден.")
        role = supported_role(conn, role_id)
        protect_last_active_role(users, target, bool(is_active) and role.role_name == target.role_name)
        if user_id == actor_id and not is_active:
            raise ServiceError("Нельзя отключить свою текущую учётную запись.")
        return users.update(user_id, full_name, role_id, is_active)


def delete_user(actor_id, user_id):
    with session(write=True) as conn:
        require_manager(conn, actor_id)
        users = UserRepository(conn)
        target = users.get_by_id(user_id)
        if target is None:
            raise ServiceError("Пользователь не найден.")
        protect_last_active_role(users, target, False)
        if user_id == actor_id:
            raise ServiceError("Нельзя удалить свою текущую учётную запись.")
        return users.delete(user_id)
