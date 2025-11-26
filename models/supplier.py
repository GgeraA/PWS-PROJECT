import psycopg2
from config import Config

class Supplier:
    def __init__(self, supplier_id=None, name=None, phone=None, contact=None, email=None, address=None):
        self.supplier_id = supplier_id
        self.name = name
        self.phone = phone
        self.contact = contact
        self.email = email
        self.address = address

    @staticmethod
    def from_row(row):
        if not row:
            return None
        return Supplier(
            supplier_id=row[0],
            name=row[1],
            phone=row[2],
            contact=row[3],
            email=row[4],
            address=row[5]
        )

    def to_dict(self):
        return {
            "supplier_id": self.supplier_id,
            "name": self.name,
            "phone": self.phone,
            "contact": self.contact,
            "email": self.email or "",
            "address": self.address or ""
        }