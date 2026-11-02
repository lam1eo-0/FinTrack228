from models import User


SELECT_USERS = """
    SELECT u.user_id, u.username, u.password_hash, u.full_name,
           u.is_active, u.role_id, r.role_name
    FROM Users AS u JOIN Roles AS r ON r.role_id = u.role_id
"""


class UserRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_all(self):
        return [User(**dict(row)) for row in self.conn.execute(SELECT_USERS + " ORDER BY u.user_id")]

    def get_by_id(self, user_id):
        row = self.conn.execute(SELECT_USERS + " WHERE u.user_id = ?", (user_id,)).fetchone()
        return User(**dict(row)) if row else None

    def get_by_username(self, username):
        row = self.conn.execute(
            SELECT_USERS + " WHERE u.username = ? COLLATE NOCASE", (username,)
        ).fetchone()
        return User(**dict(row)) if row else None

    def create(self, username, password_hash, full_name, role_id):
        cursor = self.conn.execute(
            "INSERT INTO Users(username, password_hash, full_name, role_id) VALUES (?, ?, ?, ?)",
            (username, password_hash, full_name, role_id),
        )
        return self.get_by_id(cursor.lastrowid)

    def update(self, user_id, full_name, role_id, is_active):
        self.conn.execute(
            "UPDATE Users SET full_name = ?, role_id = ?, is_active = ? WHERE user_id = ?",
            (full_name, role_id, is_active, user_id),
        )
        return self.get_by_id(user_id)

    def change_password(self, user_id, password_hash):
        self.conn.execute("UPDATE Users SET password_hash = ? WHERE user_id = ?", (password_hash, user_id))

    def count_active_accountants(self):
        return self.conn.execute(
            """SELECT COUNT(*) FROM Users u JOIN Roles r ON r.role_id = u.role_id
               WHERE u.is_active = 1 AND r.role_name = 'Бухгалтер'"""
        ).fetchone()[0]

    def delete(self, user_id):
        return self.conn.execute("DELETE FROM Users WHERE user_id = ?", (user_id,)).rowcount > 0
