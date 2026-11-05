from repositories.category_repository import CategoryRepository
from services.common import ServiceError, require_user, required_text, session, valid_type


def list_categories(actor_id, operation_type=""):
    if operation_type:
        valid_type(operation_type)
    with session() as conn:
        require_user(conn, actor_id)
        categories = CategoryRepository(conn).get_all()
        if not operation_type:
            return categories
        return [item for item in categories if item.operation_type == operation_type]


def save_category(actor_id, name, operation_type, category_id=None):
    name = required_text(name, "Название категории")
    valid_type(operation_type)
    with session(write=True) as conn:
        require_user(conn, actor_id, accountant=True)
        categories = CategoryRepository(conn)
        if category_id is not None:
            old = categories.get_by_id(category_id)
            if old is None:
                raise ServiceError("Категория не найдена.")
            if old.operation_type != operation_type and categories.is_used(category_id):
                raise ServiceError("Тип используемой категории менять нельзя. Создайте новую категорию.")
        if categories.find_duplicate(name, operation_type, category_id or 0):
            raise ServiceError("Такая категория уже существует.")
        if category_id is None:
            return categories.create(name, operation_type)
        return categories.update(category_id, name, operation_type)


def delete_category(actor_id, category_id):
    with session(write=True) as conn:
        require_user(conn, actor_id, accountant=True)
        categories = CategoryRepository(conn)
        if categories.get_by_id(category_id) is None:
            raise ServiceError("Категория не найдена.")
        if categories.is_used(category_id):
            raise ServiceError("Категория используется в операциях и не может быть удалена.")
        return categories.delete(category_id)
