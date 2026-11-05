import hashlib
import hmac
import secrets

from repositories.role_repository import RoleRepository
from repositories.user_repository import UserRepository
from services.common import (
    ACCOUNTANT, MANAGER, ServiceError, require_user, required_text, session, valid_username,
)


ITERATIONS = 260000
REGISTRATION_ROLES = (ACCOUNTANT, MANAGER)


def hash_password(password):
    if not 8 <= len(password) <= 128:
        raise ServiceError("Пароль должен содержать от 8 до 128 символов.")
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest.hex()}"


def verify_password(password, stored):
    try:
        algorithm, rounds, salt, expected = stored.split("$")
        rounds = int(rounds)
        if algorithm != "pbkdf2_sha256" or not 1 <= rounds <= 1000000 or len(password) > 128:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), rounds).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def authenticate(username, password):
    with session() as conn:
        user = UserRepository(conn).get_by_username(username.strip().lower())
        if user is None or not verify_password(password, user.password_hash):
            raise ServiceError("Неверный логин или пароль.")
        return require_user(conn, user.user_id)


def register(username, password, full_name, role_name):
    if role_name not in REGISTRATION_ROLES:
        raise ServiceError("Выберите роль бухгалтера или руководителя.")
    username = valid_username(username)
    full_name = required_text(full_name, "ФИО")
    password_hash = hash_password(password)
    with session(write=True) as conn:
        users = UserRepository(conn)
        if users.get_by_username(username):
            raise ServiceError("Пользователь с таким логином уже существует.")
        role = RoleRepository(conn).get_by_name(role_name)
        if role is None:
            raise ServiceError(f"В базе отсутствует роль «{role_name}».")
        return users.create(username, password_hash, full_name, role.role_id)


def change_password(actor_id, old_password, new_password):
    new_hash = hash_password(new_password)
    with session(write=True) as conn:
        user = require_user(conn, actor_id)
        if not verify_password(old_password, user.password_hash):
            raise ServiceError("Текущий пароль указан неверно.")
        UserRepository(conn).change_password(actor_id, new_hash)
