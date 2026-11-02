from models import Category


class CategoryRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_all(self):
        return [Category(**dict(row)) for row in self.conn.execute(
            "SELECT category_id, category_name, operation_type FROM Categories ORDER BY category_id"
        )]

    def get_by_id(self, category_id):
        row = self.conn.execute(
            "SELECT category_id, category_name, operation_type FROM Categories WHERE category_id = ?",
            (category_id,),
        ).fetchone()
        return Category(**dict(row)) if row else None

    def find_duplicate(self, name, operation_type, excluded_id=0):
        return any(
            category.category_id != excluded_id
            and category.operation_type == operation_type
            and category.category_name.strip().casefold() == name.casefold()
            for category in self.get_all()
        )

    def create(self, name, operation_type):
        cursor = self.conn.execute(
            "INSERT INTO Categories(category_name, operation_type) VALUES (?, ?)", (name, operation_type)
        )
        return self.get_by_id(cursor.lastrowid)

    def update(self, category_id, name, operation_type):
        self.conn.execute(
            "UPDATE Categories SET category_name = ?, operation_type = ? WHERE category_id = ?",
            (name, operation_type, category_id),
        )
        return self.get_by_id(category_id)

    def is_used(self, category_id):
        return self.conn.execute(
            "SELECT 1 FROM Operations WHERE category_id = ? LIMIT 1", (category_id,)
        ).fetchone() is not None

    def delete(self, category_id):
        return self.conn.execute("DELETE FROM Categories WHERE category_id = ?", (category_id,)).rowcount > 0
