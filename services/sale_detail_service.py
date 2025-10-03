# services/sale_detail_service.py
from models.sale_detail import SaleDetail

def create_sale_detail(data):
    detail = SaleDetail(
        Sale_ID=data["Sale_ID"],
        Product_ID=data["Product_ID"],
        Quantity=data["Quantity"],
        Price=data["Price"]
    )
    return detail.save()

def get_all_sale_details():
    return SaleDetail.get_all()

def get_sale_detail(detail_id):
    return SaleDetail.get_by_id(detail_id)

def update_sale_detail(detail_id, data):
    detail = SaleDetail.get_by_id(detail_id)
    if not detail:
        return None
    detail.update(data)
    return detail

def delete_sale_detail(detail_id):
    return SaleDetail.delete(detail_id)
