# app/models/supplier.py
import psycopg2
from config import Config

class Supplier:
    def __init__(self, Supplier_ID=None, Name=None, Phone=None, Contact=None):
        self.Supplier_ID = Supplier_ID
        self.Name = Name
        self.Phone = Phone
        self.Contact = Contact

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
