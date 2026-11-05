"FinTrack. Консольный финансовый учёт небольшой фирмы."

import argparse
import sqlite3

import database
from services.common import ServiceError
from services.diagnostics_service import check_database
from ui.menus import application_menu


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--init", action="store_true", help="создать отсутствующую базу и завершить работу")
    actions.add_argument("--check", action="store_true", help="проверить базу и завершить работу")
    parser.add_argument("--database", help="путь к отдельному файлу SQLite")
    args = parser.parse_args()
    if args.database:
        database.configure(args.database)
    try:
        if args.init:
            database.initialize()
            print("База создана. Запустите программу без --init для работы с меню.")
            return 0
        if not database.DATABASE_PATH.is_file():
            print("База отсутствует. Создайте её командой с --init.")
            return 1
        tables, integrity, foreign_keys = check_database()
        if args.check:
            for name, count, columns in tables:
                print(f"{name}: {count} записей")
                print("Поля:", ", ".join(f"{name} {kind}" for name, kind in columns))
            print("Целостность:", integrity)
            print("Ошибки связей:", foreign_keys)
        if integrity != [("ok",)] or foreign_keys:
            print("Проверка базы выявила ошибки.")
            return 1
        if not args.check:
            application_menu()
    except FileExistsError:
        print("База уже существует. --init создаёт только новый файл.")
        return 1
    except (ServiceError, OSError, sqlite3.DatabaseError) as error:
        print(f"Ошибка: {error}")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nРабота завершена.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
