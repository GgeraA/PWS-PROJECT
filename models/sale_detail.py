# models/sale_detail.py
import psycopg2
from config import Config

class SaleDetail:
    def __init__(self, Detail_ID=None, Sale_ID=None, Product_ID=None, Quantity=0, Price=0, Subtotal=0):
        self.Detail_ID = Detail_ID
        self.Sale_ID = Sale_ID
        self.Product_ID = Product_ID
        self.Quantity = Quantity
        self.Price = Price
        self.Subtotal = Subtotal

    # Obtener todos los detalles
    @staticmethod
    def get_all():
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT Detail_ID, Sale_ID, Product_ID, Quantity, Price, Subtotal FROM Sale_Details ORDER BY Detail_ID")
        rows = cur.fetchall()
        conn.close()
        return [SaleDetail(*row) for row in rows]

    # Obtener un detalle por ID
    @staticmethod
    def get_by_id(detail_id):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT Detail_ID, Sale_ID, Product_ID, Quantity, Price, Subtotal FROM Sale_Details WHERE Detail_ID = %s", (detail_id,))
        row = cur.fetchone()
        conn.close()
        return SaleDetail(*row) if row else None

    # Crear un nuevo detalle
    def save(self):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Sale_Details (Sale_ID, Product_ID, Quantity, Price) 
            VALUES (%s, %s, %s, %s) 
            RETURNING Detail_ID, Subtotal
            """,
            (self.Sale_ID, self.Product_ID, self.Quantity, self.Price)
        )
        row = cur.fetchone()
        self.Detail_ID, self.Subtotal = row
        conn.commit()
        conn.close()
        return self

    # Actualizar un detalle
    def update(self, data):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE Sale_Details 
            SET Sale_ID = %s, Product_ID = %s, Quantity = %s, Price = %s
            WHERE Detail_ID = %s RETURNING Detail_ID
            """,
            (
                data.get("Sale_ID", self.Sale_ID),
                data.get("Product_ID", self.Product_ID),
                data.get("Quantity", self.Quantity),
                data.get("Price", self.Price),
                self.Detail_ID
            )
        )
        row = cur.fetchone()
        conn.commit()
        conn.close()
        return bool(row)

    # Eliminar un detalle
    @staticmethod
    def delete(detail_id):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("DELETE FROM Sale_Details WHERE Detail_ID = %s RETURNING Detail_ID", (detail_id,))
        row = cur.fetchone()
        conn.commit()
        conn.close()
        return bool(row)
