# app/services/product_service.py
from models.Product import Product

# Crear producto
def create_product(data):
    product = Product(
        Code=data['Code'],
        Name=data['Name'],
        Description=data.get('Description'),
        Category=data.get('Category'),
        Unit=data.get('Unit'),
        Minimum_Stock=data.get('Minimum_Stock', 0),
        Current_Stock=data.get('Current_Stock', 0),
        Price=data['Price']
    )
    product.save()
    return product

# Obtener todos los productos
def get_all_products():
    return Product.get_all()

# Obtener producto por ID
def get_product(product_id):
    return Product.find_by_id(product_id)

# Actualizar producto
def update_product(product_id, data):
    product = Product.find_by_id(product_id)
    if not product:
        return None
    product.Code = data.get('Code', product.Code)
    product.Name = data.get('Name', product.Name)
    product.Description = data.get('Description', product.Description)
    product.Category = data.get('Category', product.Category)
    product.Unit = data.get('Unit', product.Unit)
    product.Minimum_Stock = data.get('Minimum_Stock', product.Minimum_Stock)
    product.Current_Stock = data.get('Current_Stock', product.Current_Stock)
    product.Price = data.get('Price', product.Price)
    product.update()
    return product

# Eliminar producto
def delete_product(product_id):
    return Product.delete(product_id)
