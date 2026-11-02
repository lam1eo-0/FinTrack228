import sqlite3

with sqlite3.connect("file:fintrack.db?mode=ro", uri=True) as conn:
    for table in ("Roles", "Users", "Categories", "Operations", "Reports"):
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        columns = conn.execute(f"PRAGMA table_info({table})").fetchall()

        print(f"{table}: {count} записей")
        print("Поля:", ", ".join(column[1] for column in columns))

    print("Целостность:", conn.execute("PRAGMA integrity_check").fetchall())
    print("Ошибки связей:", conn.execute("PRAGMA foreign_key_check").fetchall())