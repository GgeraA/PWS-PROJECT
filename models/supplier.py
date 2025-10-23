# app/models/supplier.py
import psycopg2
from config import Config

class Supplier:
    def __init__(self, supplier_id=None, name=None, phone=None, contact=None):
        self.supplier_id = supplier_id
        self.name = name
        self.phone = phone
        self.contact = contact

    @staticmethod
    def from_row(row):
        if not row:
            return None
        return Supplier(
            Supplier_ID=row[0],
            Name=row[1],
            Phone=row[2],
            Contact=row[3]
        )
