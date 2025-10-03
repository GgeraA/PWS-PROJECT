# models/movement.py
import psycopg2
from config import Config

class Movement:
    def __init__(self, Movement_ID=None, Date=None, Type=None, Product_ID=None,
                 Quantity=0, Reference=None, Supplier_ID=None, User_ID=None):
        self.Movement_ID = Movement_ID
        self.Date = Date
        self.Type = Type
        self.Product_ID = Product_ID
        self.Quantity = Quantity
        self.Reference = Reference
        self.Supplier_ID = Supplier_ID
        self.User_ID = User_ID

    # ---------- CRUD BÁSICO ----------

    @staticmethod
    def get_all():
        """Devuelve todos los movimientos"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            SELECT Movement_ID, Date, Type, Product_ID, Quantity, Reference, Supplier_ID, User_ID
            FROM Movements
            ORDER BY Movement_ID
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [Movement(*row) for row in rows]

    @staticmethod
    def find_by_id(movement_id):
        """Busca movimiento por ID"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            SELECT Movement_ID, Date, Type, Product_ID, Quantity, Reference, Supplier_ID, User_ID
            FROM Movements WHERE Movement_ID=%s
        """, (movement_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return Movement(*row)
        return None

    def save(self):
        """Inserta un nuevo movimiento"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Movements (Type, Product_ID, Quantity, Reference, Supplier_ID, User_ID)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING Movement_ID
        """, (self.Type, self.Product_ID, self.Quantity, self.Reference, self.Supplier_ID, self.User_ID))
        self.Movement_ID = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return self.Movement_ID

    def update(self):
        """Actualiza movimiento existente"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            UPDATE Movements
            SET Type=%s, Product_ID=%s, Quantity=%s, Reference=%s, Supplier_ID=%s, User_ID=%s
            WHERE Movement_ID=%s
        """, (self.Type, self.Product_ID, self.Quantity, self.Reference, self.Supplier_ID, self.User_ID, self.Movement_ID))
        conn.commit()
        cur.close()
        conn.close()
        return self.Movement_ID

    @staticmethod
    def delete(movement_id):
        """Elimina movimiento por ID"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("DELETE FROM Movements WHERE Movement_ID=%s RETURNING Movement_ID", (movement_id,))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return bool(row)
