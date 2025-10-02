import psycopg2
from config import Config

class Product:
    def __init__(self, Product_ID=None, Code=None, Name=None, Description=None,
                 Category=None, Unit=None, Minimum_Stock=0, Current_Stock=0, Price=0.0):
        self.Product_ID = Product_ID
        self.Code = Code
        self.Name = Name
        self.Description = Description
        self.Category = Category
        self.Unit = Unit
        self.Minimum_Stock = Minimum_Stock
        self.Current_Stock = Current_Stock
        self.Price = Price

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
        """, (self.Code, self.Name, self.Description, self.Category, self.Unit,
              self.Minimum_Stock, self.Current_Stock, self.Price))
        self.Product_ID = cur.fetchone()[0]
        conn.commit()
        conn.close()
        return self.Product_ID

    def update(self):
        """Actualiza producto existente"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            UPDATE Products
            SET Code=%s, Name=%s, Description=%s, Category=%s, Unit=%s,
                Minimum_Stock=%s, Current_Stock=%s, Price=%s
            WHERE Product_ID=%s
        """, (self.Code, self.Name, self.Description, self.Category, self.Unit,
              self.Minimum_Stock, self.Current_Stock, self.Price, self.Product_ID))
        conn.commit()
        conn.close()
        return self.Product_ID

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
