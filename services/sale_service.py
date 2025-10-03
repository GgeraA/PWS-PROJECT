# services/sale_service.py
from models.sale import Sale

def create_sale(data):
    sale = Sale(User_ID=data["User_ID"], Total=data.get("Total", 0))
    return sale.save()

def get_all_sales():
    return Sale.get_all()

def get_sale(sale_id):
    return Sale.get_by_id(sale_id)

def update_sale(sale_id, data):
    sale = Sale.get_by_id(sale_id)
    if not sale:
        return None
    sale.update(data)
    return sale

def delete_sale(sale_id):
    return Sale.delete(sale_id)
