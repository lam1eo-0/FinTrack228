from getpass import getpass
import sys

from services.common import ServiceError


def ask(label, default=None):
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{label}{suffix}: ").strip()
    return default if value == "" and default is not None else value


def ask_int(label, default=None):
    try:
        return int(ask(label, default))
    except ValueError as error:
        raise ServiceError("Введите целое число.") from error


def password(label="Пароль"):
    if sys.stdin.isatty():
        return getpass(f"{label}: ")
    return input(f"{label}: ")


def new_password():
    value = password()
    if value != password("Повторите пароль"):
        raise ServiceError("Пароли не совпадают.")
    return value


def confirm(label):
    return ask(f"{label} (да/нет)").casefold() in ("да", "д", "yes", "y")


def menu(title, actions):
    while True:
        print(f"\n=== {title} ===")
        for number, (label, _) in enumerate(actions, 1):
            print(f"{number}. {label}")
        print("0. Назад / выход")
        choice = ask("Выберите действие")
        if choice == "0":
            return
        try:
            index = int(choice) - 1
            if not 0 <= index < len(actions):
                raise ServiceError("Такого пункта меню нет.")
            actions[index][1]()
        except ValueError:
            print("Ошибка: введите номер пункта меню.")
        except ServiceError as error:
            print(f"Ошибка: {error}")
