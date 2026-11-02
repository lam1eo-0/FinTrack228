from contextlib import contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation
import re
import sqlite3

from database import get_connection
from repositories.user_repository import UserRepository


ACCOUNTANT = "Бухгалтер"
MANAGER = "Руководитель"


class ServiceError(Exception):
    """Ошибка, которую можно показать пользователю."""


@contextmanager
def session(write=False):
    try:
        with get_connection(write) as conn:
            yield conn
    except sqlite3.IntegrityError as error:
        raise ServiceError("Изменение нарушает ограничения базы: запись дублируется, используется или содержит неверные данные.") from error
    except sqlite3.OperationalError as error:
        raise ServiceError("База недоступна или занята. Проверьте путь к базе и повторите действие.") from error
    except sqlite3.DatabaseError as error:
        raise ServiceError("Ошибка структуры базы. Запустите программу с --check.") from error


def require_user(conn, actor_id, accountant=False):
    user = UserRepository(conn).get_by_id(actor_id)
    if user is None or not user.is_active:
        raise ServiceError("Пользователь отсутствует или отключён. Выполните вход заново.")
    if user.role_name not in (ACCOUNTANT, MANAGER):
        raise ServiceError("Роль пользователя не поддерживается.")
    if accountant and user.role_name != ACCOUNTANT:
        raise ServiceError("Это действие доступно только бухгалтеру.")
    return user


def required_text(value, label, max_length=200):
    value = value.strip()
    if not value:
        raise ServiceError(f"{label} не может быть пустым.")
    if len(value) > max_length:
        raise ServiceError(f"{label}: максимум {max_length} символов.")
    return value


def valid_date(value):
    value = value.strip()
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ServiceError("Введите существующую дату в формате ГГГГ-ММ-ДД.") from error
    if parsed.isoformat() != value:
        raise ServiceError("Введите дату в формате ГГГГ-ММ-ДД.")
    return value


def valid_period(start, end):
    start, end = valid_date(start), valid_date(end)
    if start > end:
        raise ServiceError("Начало периода должно быть не позже конца.")
    return start, end


def valid_amount(value):
    try:
        amount = Decimal(str(value).strip().replace(",", "."))
        if not amount.is_finite() or amount <= 0 or amount > Decimal("999999999999.99"):
            raise ServiceError("Сумма должна быть больше нуля и не превышать 999999999999.99.")
        if amount != amount.quantize(Decimal("0.01")):
            raise ServiceError("Укажите сумму с точностью до двух знаков после запятой.")
    except InvalidOperation as error:
        raise ServiceError("Сумма должна быть числом.") from error
    return float(amount)


def valid_username(value):
    value = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9_]{3,40}", value):
        raise ServiceError("Логин: 3–40 латинских букв, цифр или символов подчёркивания.")
    return value


def valid_type(value):
    if value not in ("income", "expense"):
        raise ServiceError("Тип должен быть income или expense.")
    return value
