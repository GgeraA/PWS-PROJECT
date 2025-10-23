import psycopg2
from config import Config

class Product:
    def __init__(self, product_id=None, code=None, name=None, description=None,
                 category=None, unit=None, minimum_stock=0, current_stock=0, price=0.0):
        self.product_id = product_id
        self.code = code
        self.name = name
        self.description = description
        self.category = category
        self.unit = unit
        self.minimum_stock = minimum_stock
        self.current_stock = current_stock
        self.price = price

    # ---------- CRUD BÁSICO ----------


    @staticmethod
    def get_all():
        """Devuelve todos los productos"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            SELECT Product_ID, Code, Name, Description, Category, Unit, Minimum_Stock, Current_Stock, Price
            FROM Products
            ORDER BY Product_ID
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [Product(*row) for row in rows]

    @staticmethod
    def find_by_id(product_id):
        """Busca producto por ID"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            SELECT Product_ID, Code, Name, Description, Category, Unit, Minimum_Stock, Current_Stock, Price
            FROM Products WHERE Product_ID=%s
        """, (product_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return Product(*row)
        return None

    def save(self):
        """Inserta un nuevo producto"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Products (Code, Name, Description, Category, Unit, Minimum_Stock, Current_Stock, Price)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING Product_ID
        """, (self.code, self.name, self.description, self.category, self.unit,
              self.minimum_stock, self.current_stock, self.price))
        self.product_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        return self.product_id

    def update(self):
        """Actualiza producto existente"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            UPDATE Products
            SET Code=%s, Name=%s, Description=%s, Category=%s, Unit=%s,
                minimum_stock=%s, current_stock=%s, price=%s
            WHERE product_id=%s
        """, (self.code, self.name, self.description, self.category, self.unit,
              self.minimum_stock, self.current_stock, self.price, self.product_id))
        conn.commit()
        conn.close()
        return self.product_id

    @staticmethod
    def delete(product_id):
        """Elimina producto por ID"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("DELETE FROM Products WHERE Product_ID=%s RETURNING Product_ID", (product_id,))
        row = cur.fetchone()
        conn.commit()
        conn.close()
        return bool(row)
