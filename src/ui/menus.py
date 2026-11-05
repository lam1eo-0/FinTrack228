from services import category_service, operation_service, report_service, user_service
from services.common import ACCOUNTANT, MANAGER, ServiceError
from ui import auth
from ui.common import ask, ask_int, confirm, menu, new_password


def show_categories(actor_id, operation_type=""):
    categories = category_service.list_categories(actor_id, operation_type)
    for item in categories:
        print(f"{item.category_id}. {item.category_name} ({item.operation_type})")
    return categories


def ask_type(default=None):
    print("1. Доход (income)   2. Расход (expense)")
    value = ask("Тип категории", default)
    value = {"1": "income", "2": "expense"}.get(value, value)
    if value not in ("income", "expense"):
        raise ServiceError("Выберите 1 или 2.")
    return value


def edit_category(actor_id, editing=False):
    category_id, old_name, old_type = None, None, None
    if editing:
        show_categories(actor_id)
        category_id = ask_int("ID категории")
        old = next((item for item in category_service.list_categories(actor_id)
                    if item.category_id == category_id), None)
        if old is None:
            raise ServiceError("Категория не найдена.")
        old_name, old_type = old.category_name, old.operation_type
    name = ask("Название", old_name)
    operation_type = ask_type(old_type)
    item = category_service.save_category(actor_id, name, operation_type, category_id)
    print(f"Категория {item.category_id} сохранена.")


def delete_category(actor_id):
    category_id = ask_int("ID категории")
    if confirm("Удалить категорию"):
        category_service.delete_category(actor_id, category_id)
        print("Категория удалена.")


def categories_menu(actor_id):
    menu("Категории", [
        ("Список категорий", lambda: show_categories(actor_id)),
        ("Добавить категорию", lambda: edit_category(actor_id)),
        ("Изменить категорию", lambda: edit_category(actor_id, editing=True)),
        ("Удалить категорию", lambda: delete_category(actor_id)),
    ])


def print_operations(items):
    if not items:
        print("Операций нет.")
    for item in items:
        print(f"#{item.operation_id} | {item.operation_date} | {item.operation_type} | "
              f"{item.amount:.2f} | {item.category_name} | {item.author_name}")
        print(f"  {item.description or 'Без описания'}")


def show_operations(actor_id):
    print_operations(operation_service.list_operations(actor_id))


def search_operations(actor_id):
    query = ask("Текст в описании или категории (пусто — любой)")
    start = ask("С даты ГГГГ-ММ-ДД", "0001-01-01")
    end = ask("По дату ГГГГ-ММ-ДД", "9999-12-31")
    operation_type = ask("Тип income/expense (пусто — любой)")
    print_operations(operation_service.list_operations(actor_id, start, end, query, operation_type))


def edit_operation(actor_id, operation_type="", editing=False):
    old = None
    if editing:
        old = operation_service.get_operation(actor_id, ask_int("ID операции"))
        operation_type = old.operation_type
    categories = show_categories(actor_id, operation_type)
    if not categories:
        raise ServiceError("Нет категорий для этого типа операции. Добавьте категорию в меню управления.")
    category_id = ask_int("ID категории", old.category_id if old else None)
    if not any(item.category_id == category_id for item in categories):
        raise ServiceError("Выберите ID из показанного списка категорий.")
    amount = ask("Сумма", old.amount if old else None)
    operation_date = ask("Дата ГГГГ-ММ-ДД", old.operation_date if old else None)
    description = ask("Описание", old.description if old else None)
    item = operation_service.save_operation(
        actor_id, category_id, amount, operation_date, description,
        operation_id=old.operation_id if old else None, expected_type=operation_type,
    )
    print(f"Операция {item.operation_id} сохранена.")


def delete_operation(actor_id):
    operation_id = ask_int("ID операции")
    if confirm("Удалить операцию"):
        operation_service.delete_operation(actor_id, operation_id)
        print("Операция удалена. Сохранённые отчёты остаются снимками прежних итогов.")


def print_totals(item):
    print(f"Период {item.period_start} — {item.period_end}")
    print(f"Доходы {item.total_income:.2f}, расходы {item.total_expense:.2f}, прибыль {item.profit:.2f}")


def show_summary(actor_id):
    start = ask("Начало периода ГГГГ-ММ-ДД")
    end = ask("Конец периода ГГГГ-ММ-ДД")
    print_totals(report_service.get_summary(actor_id, start, end))


def show_reports(actor_id):
    items = report_service.list_reports(actor_id)
    if not items:
        print("Отчётов нет.")
    for item in items:
        print(f"#{item.report_id} {item.report_name} | автор {item.author_name} | создан {item.created_at} UTC")
        print_totals(item)


def edit_report(actor_id, editing=False):
    old = None
    if editing:
        old = report_service.get_report(actor_id, ask_int("ID отчёта"))
    name = ask("Название", old.report_name if old else None)
    start = ask("Начало периода ГГГГ-ММ-ДД", old.period_start if old else None)
    end = ask("Конец периода ГГГГ-ММ-ДД", old.period_end if old else None)
    item = report_service.save_report(actor_id, name, start, end, old.report_id if old else None)
    print(f"Отчёт {item.report_id} сохранён с актуальными итогами.")
    print_totals(item)


def delete_report(actor_id):
    report_id = ask_int("ID отчёта")
    if confirm("Удалить отчёт"):
        report_service.delete_report(actor_id, report_id)
        print("Отчёт удалён.")


def reports_menu(actor_id):
    menu("Отчёты", [
        ("Список отчётов", lambda: show_reports(actor_id)),
        ("Сформировать отчёт", lambda: edit_report(actor_id)),
        ("Изменить период/название и пересчитать отчёт", lambda: edit_report(actor_id, editing=True)),
        ("Удалить отчёт", lambda: delete_report(actor_id)),
    ])


def show_roles(actor_id):
    for role in user_service.list_roles(actor_id):
        print(f"{role.role_id}. {role.role_name} — {role.description or ''}")


def show_users(actor_id):
    for user in user_service.list_users(actor_id):
        state = "активен" if user.is_active else "отключён"
        print(f"#{user.user_id} {user.username} | {user.full_name} | {user.role_name} | {state}")


def create_user(actor_id):
    username = ask("Логин нового пользователя")
    full_name = ask("ФИО")
    secret = new_password()
    show_roles(actor_id)
    role_id = ask_int("ID роли")
    user = user_service.create_user(actor_id, username, secret, full_name, role_id)
    print(f"Пользователь {user.username} создан.")


def edit_user(actor_id):
    show_users(actor_id)
    user_id = ask_int("ID пользователя")
    old = next((user for user in user_service.list_users(actor_id) if user.user_id == user_id), None)
    if old is None:
        raise ServiceError("Пользователь не найден.")
    name = ask("ФИО", old.full_name)
    show_roles(actor_id)
    role_id = ask_int("ID роли", old.role_id)
    is_active = ask_int("Активен 1 / отключён 0", old.is_active)
    user_service.update_user(actor_id, user_id, name, role_id, is_active)
    print("Данные пользователя сохранены.")


def delete_user(actor_id):
    user_id = ask_int("ID пользователя")
    if confirm("Удалить пользователя"):
        user_service.delete_user(actor_id, user_id)
        print("Пользователь удалён.")


def users_menu(actor_id):
    menu("Пользователи", [
        ("Список пользователей", lambda: show_users(actor_id)),
        ("Добавить пользователя", lambda: create_user(actor_id)),
        ("Изменить ФИО, роль или активность", lambda: edit_user(actor_id)),
        ("Удалить пользователя без связанных операций и отчётов", lambda: delete_user(actor_id)),
        ("Список системных ролей", lambda: show_roles(actor_id)),
    ])


def user_menu(actor_id):
    user = user_service.current_user(actor_id)
    actions = [
        ("Просмотр операций", lambda: show_operations(actor_id)),
        ("Поиск операций", lambda: search_operations(actor_id)),
        ("Финансовые показатели за период", lambda: show_summary(actor_id)),
        ("Просмотр отчётов", lambda: show_reports(actor_id)),
        ("Просмотр категорий", lambda: browse_categories(actor_id)),
        ("Сменить свой пароль", lambda: auth.change_password(actor_id)),
    ]
    if user.role_name == ACCOUNTANT:
        actions += [
            ("Добавить доход", lambda: edit_operation(actor_id, "income")),
            ("Добавить расход", lambda: edit_operation(actor_id, "expense")),
            ("Изменить операцию", lambda: edit_operation(actor_id, editing=True)),
            ("Удалить операцию", lambda: delete_operation(actor_id)),
            ("Управление категориями", lambda: categories_menu(actor_id)),
            ("Управление отчётами", lambda: reports_menu(actor_id)),
        ]
    elif user.role_name == MANAGER:
        actions.append(("Управление пользователями", lambda: users_menu(actor_id)))
    print(f"\nВыполнен вход: {user.full_name} ({user.role_name})")
    menu("FinTrack", actions)


def application_menu():
    def sign_in():
        user = auth.login()
        user_menu(user.user_id)

    menu("Добро пожаловать в FinTrack", [
        ("Войти", sign_in),
        ("Зарегистрироваться", auth.register),
    ])


def browse_categories(actor_id):
    categories = category_service.list_categories(actor_id)
    if not categories:
        print("Категорий нет.")
        return

    def show_category_operations(category):
        print(f"\nОперации категории «{category.category_name}»")
        print_operations(operation_service.list_operations(actor_id, category_id=category.category_id))

    menu("Выберите категорию", [
        (f"{item.category_name} ({item.operation_type})", lambda item=item: show_category_operations(item))
        for item in categories
    ])
