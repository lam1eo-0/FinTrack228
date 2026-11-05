from models import Operation


SELECT_OPERATIONS = """
    SELECT o.operation_id, o.user_id, o.category_id, o.amount,
           o.operation_date, o.description, c.category_name,
           c.operation_type, u.full_name AS author_name
    FROM Operations o
    JOIN Categories c ON c.category_id = o.category_id
    JOIN Users u ON u.user_id = o.user_id
"""


class OperationRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_id(self, operation_id):
        row = self.conn.execute(SELECT_OPERATIONS + " WHERE o.operation_id = ?", (operation_id,)).fetchone()
        return Operation(**dict(row)) if row else None

    def get_all(self, start="0001-01-01", end="9999-12-31", query="", operation_type="", *, category_id=None):
        rows = self.conn.execute(
            SELECT_OPERATIONS + """
            WHERE o.operation_date BETWEEN ? AND ?
              AND (? = '' OR c.operation_type = ?)
              AND (? IS NULL OR o.category_id = ?)
            ORDER BY o.operation_date DESC, o.operation_id DESC
            """, (start, end, operation_type, operation_type, category_id, category_id)
        )
        operations = [Operation(**dict(row)) for row in rows]
        needle = query.casefold()
        return [operation for operation in operations if
                needle in (operation.description or "").casefold()
                or needle in operation.category_name.casefold()]

    def create(self, user_id, category_id, amount, operation_date, description):
        cursor = self.conn.execute(
            """INSERT INTO Operations(user_id, category_id, amount, operation_date, description)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, category_id, amount, operation_date, description),
        )
        return self.get_by_id(cursor.lastrowid)

    def update(self, operation_id, category_id, amount, operation_date, description):
        self.conn.execute(
            """UPDATE Operations SET category_id = ?, amount = ?, operation_date = ?, description = ?
               WHERE operation_id = ?""", (category_id, amount, operation_date, description, operation_id)
        )
        return self.get_by_id(operation_id)

    def delete(self, operation_id):
        return self.conn.execute("DELETE FROM Operations WHERE operation_id = ?", (operation_id,)).rowcount > 0

    def get_totals(self, start, end):
        row = self.conn.execute(
            """SELECT
                ROUND(COALESCE(SUM(CASE WHEN c.operation_type = 'income' THEN o.amount ELSE 0 END), 0), 2),
                ROUND(COALESCE(SUM(CASE WHEN c.operation_type = 'expense' THEN o.amount ELSE 0 END), 0), 2)
               FROM Operations o JOIN Categories c ON c.category_id = o.category_id
               WHERE o.operation_date BETWEEN ? AND ?""", (start, end)
        ).fetchone()
        return row[0], row[1]
