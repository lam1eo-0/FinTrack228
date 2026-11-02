from models import Report


SELECT_REPORTS = """
    SELECT r.report_id, r.user_id, r.report_name, r.period_start, r.period_end,
           r.created_at, r.total_income, r.total_expense, r.profit, u.full_name AS author_name
    FROM Reports r JOIN Users u ON u.user_id = r.user_id
"""


class ReportRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_all(self):
        return [Report(**dict(row)) for row in self.conn.execute(
            SELECT_REPORTS + " ORDER BY r.report_id DESC"
        )]

    def get_by_id(self, report_id):
        row = self.conn.execute(SELECT_REPORTS + " WHERE r.report_id = ?", (report_id,)).fetchone()
        return Report(**dict(row)) if row else None

    def create(self, user_id, name, summary):
        cursor = self.conn.execute(
            """INSERT INTO Reports(user_id, report_name, period_start, period_end,
                                   total_income, total_expense, profit)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, name, summary.period_start, summary.period_end,
             summary.total_income, summary.total_expense, summary.profit),
        )
        return self.get_by_id(cursor.lastrowid)

    def update(self, report_id, user_id, name, summary):
        self.conn.execute(
            """UPDATE Reports SET user_id = ?, report_name = ?, period_start = ?, period_end = ?,
               total_income = ?, total_expense = ?, profit = ?, created_at = CURRENT_TIMESTAMP
               WHERE report_id = ?""",
            (user_id, name, summary.period_start, summary.period_end,
             summary.total_income, summary.total_expense, summary.profit, report_id),
        )
        return self.get_by_id(report_id)

    def delete(self, report_id):
        return self.conn.execute("DELETE FROM Reports WHERE report_id = ?", (report_id,)).rowcount > 0
