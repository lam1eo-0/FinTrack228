from repositories.category_repository import CategoryRepository
from repositories.operation_repository import OperationRepository
from services.common import (
    ServiceError, require_user, session, valid_amount, valid_date, valid_period, valid_type,
)


def list_operations(actor_id, start="0001-01-01", end="9999-12-31", query="", operation_type=""):
    start, end = valid_period(start, end)
    if operation_type:
        valid_type(operation_type)
    with session() as conn:
        require_user(conn, actor_id)
        return OperationRepository(conn).get_all(start, end, query.strip(), operation_type)


def get_operation(actor_id, operation_id):
    with session() as conn:
        require_user(conn, actor_id)
        operation = OperationRepository(conn).get_by_id(operation_id)
        if operation is None:
            raise ServiceError("Операция не найдена.")
        return operation


def save_operation(actor_id, category_id, amount, operation_date, description="", operation_id=None, expected_type=""):
    amount = valid_amount(amount)
    operation_date = valid_date(operation_date)
    if expected_type:
        valid_type(expected_type)
    description = description.strip()
    if len(description) > 1000:
        raise ServiceError("Описание: максимум 1000 символов.")
    with session(write=True) as conn:
        require_user(conn, actor_id, accountant=True)
        category = CategoryRepository(conn).get_by_id(category_id)
        if category is None:
            raise ServiceError("Категория не найдена.")
        if expected_type and category.operation_type != expected_type:
            raise ServiceError("Выбранная категория не соответствует доходу или расходу.")
        operations = OperationRepository(conn)
        if operation_id is None:
            return operations.create(actor_id, category_id, amount, operation_date, description)
        if operations.get_by_id(operation_id) is None:
            raise ServiceError("Операция не найдена.")
        return operations.update(operation_id, category_id, amount, operation_date, description)


def delete_operation(actor_id, operation_id):
    with session(write=True) as conn:
        require_user(conn, actor_id, accountant=True)
        operations = OperationRepository(conn)
        if operations.get_by_id(operation_id) is None:
            raise ServiceError("Операция не найдена.")
        return operations.delete(operation_id)
