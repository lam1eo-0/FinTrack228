"""Подключение, транзакции и создание базы."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parents[1] / "fintrack.db"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema.sql"


def configure(path):
    global DATABASE_PATH
    DATABASE_PATH = Path(path).resolve()


@contextmanager
def get_connection(write=False):
    """Транзакция охватывает проверки сервиса и все вызовы репозиториев."""
    mode = "rw" if write else "ro"
    conn = sqlite3.connect(DATABASE_PATH.as_uri() + f"?mode={mode}", uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize():
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with DATABASE_PATH.open("xb"):
        pass
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.executescript(schema)
    except Exception:
        if conn is not None:
            conn.close()
        DATABASE_PATH.unlink()
        raise
    finally:
        if conn is not None:
            conn.close()
