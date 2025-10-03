# app/services/supplier_service.py
import psycopg2
from config import Config
from models.supplier import Supplier

def get_all_suppliers():
    conn = psycopg2.connect(**Config.DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT Supplier_ID, Name, Phone, Contact FROM Suppliers ORDER BY Supplier_ID")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [Supplier.from_row(r) for r in rows]

def get_supplier(supplier_id):
    conn = psycopg2.connect(**Config.DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT Supplier_ID, Name, Phone, Contact FROM Suppliers WHERE Supplier_ID = %s", (supplier_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return Supplier.from_row(row)

def create_supplier(data):
    conn = psycopg2.connect(**Config.DATABASE)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO Suppliers (Name, Phone, Contact)
        VALUES (%s, %s, %s) RETURNING Supplier_ID
        """,
        (data.get("Name"), data.get("Phone"), data.get("Contact"))
    )
    supplier_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return get_supplier(supplier_id)

def update_supplier(supplier_id, data):
    conn = psycopg2.connect(**Config.DATABASE)
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE Suppliers
        SET Name = %s, Phone = %s, Contact = %s
        WHERE Supplier_ID = %s RETURNING Supplier_ID
        """,
        (data.get("Name"), data.get("Phone"), data.get("Contact"), supplier_id)
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return get_supplier(supplier_id) if row else None

def delete_supplier(supplier_id):
    conn = psycopg2.connect(**Config.DATABASE)
    cur = conn.cursor()
    cur.execute("DELETE FROM Suppliers WHERE Supplier_ID = %s RETURNING Supplier_ID", (supplier_id,))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return bool(row)
