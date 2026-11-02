"""Создание учебной базы и проверка её структуры и целостности."""

import argparse
from pathlib import Path
import sqlite3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init", action="store_true", help="создать отсутствующую БД из schema.sql")
    args = parser.parse_args()
    source_dir = Path(__file__).resolve().parent
    database_path = source_dir / "fintrack.db"

    if args.init:
        schema = (source_dir / "schema.sql").read_text(encoding="utf-8")
        try:
            with database_path.open("xb"):
                pass
        except FileExistsError:
            parser.exit(1, "База уже существует. Для пересоздания сначала переместите её в резервную копию.\n")
        conn = None
        try:
            with sqlite3.connect(database_path) as conn:
                conn.executescript(schema)
        except Exception:
            if conn is not None:
                conn.close()
            database_path.unlink()
            raise
        conn.close()
        print("База создана из schema.sql.")

    try:
        conn = sqlite3.connect(database_path.as_uri() + "?mode=ro", uri=True)
    except sqlite3.OperationalError:
        parser.exit(1, "Не удалось открыть базу рядом с main.py. Создать её можно командой с --init.\n")

    try:
        conn.execute("PRAGMA foreign_keys = ON")
        for table in ("Roles", "Users", "Categories", "Operations", "Reports"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
            print(f"{table}: {count} записей")
            print("Поля:", ", ".join(f"{column[1]} {column[2]}" for column in columns))

        integrity = conn.execute("PRAGMA integrity_check").fetchall()
        foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
        print("Целостность:", integrity)
        print("Ошибки связей:", foreign_keys)
        if integrity != [("ok",)] or foreign_keys:
            parser.exit(1, "Проверка базы выявила ошибки.\n")
    except sqlite3.DatabaseError as error:
        parser.exit(1, f"Ошибка базы данных: {error}\n")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
