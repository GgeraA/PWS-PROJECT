import psycopg2
from config import Config
from models.supplier import Supplier

def get_all_suppliers():
    conn = psycopg2.connect(**Config.get_database_config())
    cur = conn.cursor()
    cur.execute("SELECT supplier_id, name, phone, contact, email, address FROM suppliers ORDER BY supplier_id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    suppliers = []
    for row in rows:
        supplier = Supplier.from_row(row)
        suppliers.append(supplier.to_dict())
    return suppliers

def get_supplier(supplier_id):
    conn = psycopg2.connect(**Config.get_database_config())
    cur = conn.cursor()
    cur.execute("SELECT supplier_id, name, phone, contact, email, address FROM suppliers WHERE supplier_id = %s", (supplier_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        supplier = Supplier.from_row(row)
        return supplier.to_dict()
    return None

def create_supplier(data):
    conn = psycopg2.connect(**Config.get_database_config())
    cur = conn.cursor()
    
    cur.execute(
        """
        INSERT INTO suppliers (name, phone, contact, email, address)
        VALUES (%s, %s, %s, %s, %s) RETURNING supplier_id
        """,
        (
            data.get("name"), 
            data.get("phone"), 
            data.get("contact"), 
            data.get("email", ""),  # Valor por defecto vacío
            data.get("address", "") # Valor por defecto vacío
        )
    )
    supplier_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return get_supplier(supplier_id)

def update_supplier(supplier_id, data):
    conn = psycopg2.connect(**Config.get_database_config())
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE suppliers
        SET name = %s, phone = %s, contact = %s, email = %s, address = %s
        WHERE supplier_id = %s RETURNING supplier_id
        """,
        (
            data.get("name"), 
            data.get("phone"), 
            data.get("contact"), 
            data.get("email", ""), 
            data.get("address", ""), 
            supplier_id
        )
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return get_supplier(supplier_id) if row else None

def delete_supplier(supplier_id):
    conn = psycopg2.connect(**Config.get_database_config())
    cur = conn.cursor()
    cur.execute("DELETE FROM suppliers WHERE supplier_id = %s RETURNING supplier_id", (supplier_id,))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return bool(row)