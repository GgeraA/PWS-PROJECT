# models/movement.py
import psycopg2
from config import Config

class Movement:
    def __init__(self, movement_id=None, date=None, type=None, product_id=None,
                 quantity=0, reference=None, supplier_id=None, user_id=None):
        self.movement_id = movement_id
        self.date = date
        self.type = type
        self.product_id = product_id
        self.quantity = quantity
        self.reference = reference
        self.supplier_id = supplier_id
        self.user_id = user_id

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
        """, (self.type, self.product_id, self.quantity, self.reference, self.supplier_id, self.user_id))
        self.movement_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return self.movement_id

    def update(self):
        """Actualiza movimiento existente"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            UPDATE Movements
            SET Type=%s, Product_ID=%s, Quantity=%s, Reference=%s, Supplier_ID=%s, User_ID=%s
            WHERE Movement_ID=%s
        """, (self.type, self.product_id, self.quantity, self.reference, self.supplier_id, self.user_id, self.movement_id))
        conn.commit()
        cur.close()
        conn.close()
        return self.movement_id

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
