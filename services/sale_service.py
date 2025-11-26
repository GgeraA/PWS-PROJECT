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

def get_sales_with_details():
    """Obtener todas las ventas con información completa para reportes"""
    try:
        sales = Sale.get_all()
        result = []
        
        for sale in sales:
            # Obtener detalles de la venta
            from models.sale_detail import SaleDetail
            from models.Product import Product
            from models.user import User
            
            # Usar el nuevo método que acabamos de crear
            details = SaleDetail.get_by_sale_id(sale.sale_id)
            
            # Para cada detalle, crear un registro completo
            for detail in details:
                # Obtener información del producto
                product = None
                if hasattr(Product, 'get_by_id'):
                    product = Product.get_by_id(detail.product_id)
                
                # Obtener información del usuario/vendedor
                user = None
                if hasattr(User, 'get_by_id'):
                    user = User.get_by_id(sale.user_id)
                
                # Construir el objeto de respuesta
                sale_data = {
                    "id": sale.sale_id,
                    "product_id": detail.product_id,
                    "product_name": product.name if product else f"Producto {detail.product_id}",
                    "quantity": detail.quantity,
                    "unit_price": float(detail.price) if detail.price else 0,
                    "total": float(detail.subtotal) if detail.subtotal else 0,
                    "date": sale.date.isoformat() if sale.date else None,
                    "user_id": sale.user_id,
                    "seller_name": user.nombre if user else f"Vendedor {sale.user_id}",
                    "payment_method": "Efectivo"  # Valor por defecto
                }
                result.append(sale_data)
        
        return result
        
    except Exception as e:
        print(f"Error en get_sales_with_details: {e}")
        # En caso de error, devolver datos mock
        return get_mock_sales_data()

def get_mock_sales_data():
    """Datos de ejemplo para desarrollo cuando hay errores"""
    from datetime import datetime, timedelta
    import random
    
    products = [
        "Laptop HP ProBook 15",
        "Mouse Logitech MX Master 3", 
        "Teclado Mecánico Redragon",
        "Monitor Samsung 24\" FHD"
    ]
    
    sellers = ["Juan Pérez", "María García", "Carlos López", "Ana Rodríguez"]
    
    sales_data = []
    
    # Generar 10 ventas de ejemplo
    for i in range(1, 11):
        product = random.choice(products)
        quantity = random.randint(1, 3)
        unit_price = round(random.uniform(500, 20000), 2)
        total = round(quantity * unit_price, 2)
        
        # Fecha aleatoria en los últimos 30 días
        days_ago = random.randint(0, 30)
        sale_date = datetime.now() - timedelta(days=days_ago)
        
        sales_data.append({
            "id": i,
            "product_id": i,
            "product_name": product,
            "quantity": quantity,
            "unit_price": unit_price,
            "total": total,
            "date": sale_date.isoformat(),
            "user_id": random.randint(1, 4),
            "seller_name": random.choice(sellers),
            "payment_method": random.choice(["Efectivo", "Tarjeta", "Transferencia"])
        })
    
    return sales_data

def get_sales_by_filters(start_date=None, end_date=None, payment_method=None):
    """Obtener ventas filtradas por fecha y método de pago"""
    try:
        all_sales = get_sales_with_details()
        filtered_sales = all_sales
        
        # Filtrar por fecha
        if start_date:
            filtered_sales = [s for s in filtered_sales if s["date"] and s["date"] >= start_date]
        if end_date:
            filtered_sales = [s for s in filtered_sales if s["date"] and s["date"] <= end_date]
        
        # Filtrar por método de pago
        if payment_method and payment_method != "all":
            filtered_sales = [s for s in filtered_sales if s["payment_method"] == payment_method]
        
        return filtered_sales
        
    except Exception as e:
        print(f"Error en get_sales_by_filters: {e}")
        return get_mock_sales_data()