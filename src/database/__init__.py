"""Подключение, транзакции и создание базы."""

from contextlib import closing, contextmanager
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory


SEED_PATH = Path(__file__).resolve().parents[1] / "fintrack.db"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema.sql"
DATA_ROOT = os.environ.get("LOCALAPPDATA" if os.name == "nt" else "XDG_DATA_HOME")
DATABASE_PATH = ((Path(DATA_ROOT) if DATA_ROOT else Path.home() / ".local" / "share")
                 / "FinTrack228" / "fintrack.db").resolve()


def configure(path):
    global DATABASE_PATH
    DATABASE_PATH = Path(path).resolve()


def prepare_default_database():
    if DATABASE_PATH.exists() or not SEED_PATH.is_file():
        return
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=DATABASE_PATH.parent) as folder:
        staged = Path(folder) / DATABASE_PATH.name
        with closing(sqlite3.connect(SEED_PATH.as_uri() + "?mode=ro", uri=True)) as source:
            with closing(sqlite3.connect(staged)) as destination:
                source.backup(destination)
        try:
            if os.name == "nt":
                staged.rename(DATABASE_PATH)
            else:
                os.link(staged, DATABASE_PATH)
        except FileExistsError:
            # Another process prepared the same database first.
            pass


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
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
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
