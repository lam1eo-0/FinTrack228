from repositories.diagnostics_repository import inspect_database
from services.common import session


def check_database():
    with session() as conn:
        return inspect_database(conn)
