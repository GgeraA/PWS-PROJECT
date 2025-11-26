# models/sale_detail.py
import psycopg2
from config import Config

class SaleDetail:
    def __init__(self, detail_id=None, sale_id=None, product_id=None, quantity=0, price=0, subtotal=0):
        self.detail_id = detail_id
        self.sale_id = sale_id
        self.product_id = product_id
        self.quantity = quantity
        self.price = price
        self.subtotal = subtotal


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
            RETURNING detail_id, subtotal
            """,
            (self.sale_id, self.product_id, self.quantity, self.price)
        )
        row = cur.fetchone()
        self.detail_id, self.subtotal = row
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
                data.get("sale_id", self.sale_id),
                data.get("product_id", self.product_id),
                data.get("quantity", self.quantity),
                data.get("price", self.price),
                self.detail_id
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
    
    # Obtener detalles por sale_id
@staticmethod
def get_by_sale_id(sale_id):
    conn = psycopg2.connect(**Config.DATABASE)
    cur = conn.cursor()
    cur.execute("""
        SELECT Detail_ID, Sale_ID, Product_ID, Quantity, Price, Subtotal 
        FROM Sale_Details 
        WHERE Sale_ID = %s
    """, (sale_id,))
    rows = cur.fetchall()
    conn.close()
    return [SaleDetail(*row) for row in rows]
