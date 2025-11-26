import psycopg2
from config import Config

class Product:
    def __init__(self, product_id=None, code=None, name=None, description=None,
                 category=None, unit=None, minimum_stock=0, current_stock=0, price=0.0,
                 barcode=None, brand=None, cost_price=None, maximum_stock=0, 
                 tax_rate=0.0, supplier=None, location=None):
        self.product_id = product_id
        self.code = code
        self.name = name
        self.description = description
        self.category = category
        self.unit = unit
        self.minimum_stock = minimum_stock
        self.current_stock = current_stock
        self.price = price
        self.barcode = barcode
        self.brand = brand
        self.cost_price = cost_price
        self.maximum_stock = maximum_stock
        self.tax_rate = tax_rate
        self.supplier = supplier
        self.location = location

    # ---------- CRUD BÁSICO ----------

    @staticmethod
    def get_all():
        """Devuelve todos los productos"""
        conn = psycopg2.connect(**Config.get_database_config())
        cur = conn.cursor()
        cur.execute("""
            SELECT Product_ID, Code, Name, Description, Category, Unit, 
                   Minimum_Stock, Current_Stock, Price, Barcode, Brand, 
                   Cost_Price, Maximum_Stock, Tax_Rate, Supplier, Location
            FROM Products
            ORDER BY Product_ID
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        products = []
        for row in rows:
            # Crear el producto con todos los campos en el orden correcto
            product = Product(
                product_id=row[0],
                code=row[1],
                name=row[2],
                description=row[3],
                category=row[4],
                unit=row[5],
                minimum_stock=row[6],
                current_stock=row[7],
                price=row[8],
                barcode=row[9],
                brand=row[10],
                cost_price=row[11],
                maximum_stock=row[12],
                tax_rate=row[13],
                supplier=row[14],
                location=row[15]
            )
            products.append(product)
        return products

    @staticmethod
    def find_by_id(product_id):
        """Busca producto por ID"""
        conn = psycopg2.connect(**Config.get_database_config())
        cur = conn.cursor()
        cur.execute("""
            SELECT Product_ID, Code, Name, Description, Category, Unit, 
                   Minimum_Stock, Current_Stock, Price, Barcode, Brand, 
                   Cost_Price, Maximum_Stock, Tax_Rate, Supplier, Location
            FROM Products WHERE Product_ID=%s
        """, (product_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            return Product(
                product_id=row[0],
                code=row[1],
                name=row[2],
                description=row[3],
                category=row[4],
                unit=row[5],
                minimum_stock=row[6],
                current_stock=row[7],
                price=row[8],
                barcode=row[9],
                brand=row[10],
                cost_price=row[11],
                maximum_stock=row[12],
                tax_rate=row[13],
                supplier=row[14],
                location=row[15]
            )
        return None

    def save(self):
        """Inserta un nuevo producto"""
        conn = psycopg2.connect(**Config.get_database_config())
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Products 
            (Code, Name, Description, Category, Unit, Minimum_Stock, Current_Stock, Price,
             Barcode, Brand, Cost_Price, Maximum_Stock, Tax_Rate, Supplier, Location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING Product_ID
        """, (
            self.code, self.name, self.description, self.category, self.unit,
            self.minimum_stock, self.current_stock, self.price,
            self.barcode, self.brand, self.cost_price, self.maximum_stock,
            self.tax_rate, self.supplier, self.location
        ))
        self.product_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return self.product_id

    def update(self):
        """Actualiza producto existente"""
        conn = psycopg2.connect(**Config.get_database_config())
        cur = conn.cursor()
        cur.execute("""
            UPDATE Products
            SET Code=%s, Name=%s, Description=%s, Category=%s, Unit=%s,
                Minimum_Stock=%s, Current_Stock=%s, Price=%s,
                Barcode=%s, Brand=%s, Cost_Price=%s, Maximum_Stock=%s,
                Tax_Rate=%s, Supplier=%s, Location=%s
            WHERE Product_ID=%s
        """, (
            self.code, self.name, self.description, self.category, self.unit,
            self.minimum_stock, self.current_stock, self.price,
            self.barcode, self.brand, self.cost_price, self.maximum_stock,
            self.tax_rate, self.supplier, self.location, self.product_id
        ))
        conn.commit()
        cur.close()
        conn.close()
        return self.product_id

    @staticmethod
    def delete(product_id):
        """Elimina producto por ID"""
        conn = psycopg2.connect(**Config.get_database_config())
        cur = conn.cursor()
        cur.execute("DELETE FROM Products WHERE Product_ID=%s RETURNING Product_ID", (product_id,))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return bool(row)

    def to_dict(self):
        """Convierte el objeto Product a diccionario para JSON"""
        return {
            "Product_ID": self.product_id,
            "Code": self.code,
            "Name": self.name,
            "Description": self.description,
            "Category": self.category,
            "Unit": self.unit,
            "Minimum_Stock": self.minimum_stock,
            "Current_Stock": self.current_stock,
            "Price": float(self.price) if self.price else 0.0,
            "Barcode": self.barcode,
            "Brand": self.brand,
            "Cost_Price": float(self.cost_price) if self.cost_price else None,
            "Maximum_Stock": self.maximum_stock,
            "Tax_Rate": float(self.tax_rate) if self.tax_rate else 0.0,
            "Supplier": self.supplier,
            "Location": self.location
        }