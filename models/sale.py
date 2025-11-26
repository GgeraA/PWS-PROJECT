# models/sale.py
import psycopg2
from config import Config

class Sale:
    def __init__(self, sale_id=None, date=None, user_id=None, total=0):
        self.sale_id = sale_id
        self.date = date
        self.user_id = user_id
        self.total = total

    # Obtener todas las ventas
    @staticmethod
    def get_all():
        conn = psycopg2.connect(**Config.get_database_config())
        cur = conn.cursor()
        cur.execute("SELECT Sale_ID, Date, User_ID, Total FROM Sales ORDER BY Sale_ID")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [Sale(*row) for row in rows]

    # Obtener una venta por ID
    @staticmethod
    def get_by_id(sale_id):
        conn = psycopg2.connect(**Config.get_database_config())
        cur = conn.cursor()
        cur.execute("SELECT Sale_ID, Date, User_ID, Total FROM Sales WHERE Sale_ID = %s", (sale_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return Sale(*row) if row else None

    # Crear una nueva venta
    def save(self):
        conn = psycopg2.connect(**Config.get_database_config())
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Sales (User_ID, Total) VALUES (%s, %s) RETURNING Sale_ID, Date",
            (self.user_id, self.total)
        )
        row = cur.fetchone()
        self.sale_id, self.date = row
        conn.commit()
        cur.close()
        conn.close()
        return self

    # Actualizar una venta
    def update(self, data):
        conn = psycopg2.connect(**Config.get_database_config())
        cur = conn.cursor()
        cur.execute(
            "UPDATE Sales SET User_ID = %s, Total = %s WHERE Sale_ID = %s RETURNING Sale_ID",
            (data.get("User_ID", self.user_id), data.get("Total", self.total), self.sale_id)
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return bool(row)

    # Eliminar una venta
    @staticmethod
    def delete(sale_id):
        conn = psycopg2.connect(**Config.get_database_config())
        cur = conn.cursor()
        cur.execute("DELETE FROM Sales WHERE Sale_ID = %s RETURNING Sale_ID", (sale_id,))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return bool(row)