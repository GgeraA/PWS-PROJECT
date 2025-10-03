# models/sale.py
import psycopg2
from config import Config

class Sale:
    def __init__(self, Sale_ID=None, Date=None, User_ID=None, Total=0):
        self.Sale_ID = Sale_ID
        self.Date = Date
        self.User_ID = User_ID
        self.Total = Total

    # Obtener todas las ventas
    @staticmethod
    def get_all():
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT Sale_ID, Date, User_ID, Total FROM Sales ORDER BY Sale_ID")
        rows = cur.fetchall()
        conn.close()
        return [Sale(*row) for row in rows]

    # Obtener una venta por ID
    @staticmethod
    def get_by_id(sale_id):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT Sale_ID, Date, User_ID, Total FROM Sales WHERE Sale_ID = %s", (sale_id,))
        row = cur.fetchone()
        conn.close()
        return Sale(*row) if row else None

    # Crear una nueva venta
    def save(self):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Sales (User_ID, Total) VALUES (%s, %s) RETURNING Sale_ID, Date",
            (self.User_ID, self.Total)
        )
        row = cur.fetchone()
        self.Sale_ID, self.Date = row
        conn.commit()
        conn.close()
        return self

    # Actualizar una venta
    def update(self, data):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute(
            "UPDATE Sales SET User_ID = %s, Total = %s WHERE Sale_ID = %s RETURNING Sale_ID",
            (data.get("User_ID", self.User_ID), data.get("Total", self.Total), self.Sale_ID)
        )
        row = cur.fetchone()
        conn.commit()
        conn.close()
        return bool(row)

    # Eliminar una venta
    @staticmethod
    def delete(sale_id):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("DELETE FROM Sales WHERE Sale_ID = %s RETURNING Sale_ID", (sale_id,))
        row = cur.fetchone()
        conn.commit()
        conn.close()
        return bool(row)
