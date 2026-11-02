from models import Role


class RoleRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_all(self):
        rows = self.conn.execute("SELECT role_id, role_name, description FROM Roles ORDER BY role_id")
        return [Role(**dict(row)) for row in rows]

    def get_by_id(self, role_id):
        row = self.conn.execute(
            "SELECT role_id, role_name, description FROM Roles WHERE role_id = ?", (role_id,)
        ).fetchone()
        return Role(**dict(row)) if row else None

    def get_by_name(self, name):
        row = self.conn.execute(
            "SELECT role_id, role_name, description FROM Roles WHERE role_name = ?", (name,)
        ).fetchone()
        return Role(**dict(row)) if row else None

    def create(self, name, description=None):
        cursor = self.conn.execute(
            "INSERT INTO Roles(role_name, description) VALUES (?, ?)", (name, description)
        )
        return self.get_by_id(cursor.lastrowid)

    def update(self, role_id, name, description=None):
        self.conn.execute(
            "UPDATE Roles SET role_name = ?, description = ? WHERE role_id = ?",
            (name, description, role_id),
        )
        return self.get_by_id(role_id)

    def delete(self, role_id):
        return self.conn.execute("DELETE FROM Roles WHERE role_id = ?", (role_id,)).rowcount > 0
