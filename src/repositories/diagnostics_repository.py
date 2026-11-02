TABLES = ("Roles", "Users", "Categories", "Operations", "Reports")


def inspect_database(conn):
    tables = []
    for table in TABLES:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        columns = [(row[1], row[2]) for row in conn.execute(f"PRAGMA table_info({table})")]
        tables.append((table, count, columns))
    integrity = [tuple(row) for row in conn.execute("PRAGMA integrity_check")]
    foreign_keys = [tuple(row) for row in conn.execute("PRAGMA foreign_key_check")]
    return tables, integrity, foreign_keys
