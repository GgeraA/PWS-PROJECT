from models.Product import Product

def create_product(data):
    product = Product(
        code=data.get('Code'),
        name=data.get('Name'),
        description=data.get('Description'),
        category=data.get('Category'),
        unit=data.get('Unit'),
        minimum_stock=data.get('Minimum_Stock', 0),
        current_stock=data.get('Current_Stock', 0),
        price=data.get('Price', 0.0),
        barcode=data.get('Barcode'),
        brand=data.get('Brand'),
        cost_price=data.get('CostPrice'),
        maximum_stock=data.get('Maximum_Stock', 0),
        tax_rate=data.get('TaxRate', 0.0),
        supplier=data.get('Supplier'),
        location=data.get('Location')
    )
    product_id = product.save()
    return Product.find_by_id(product_id).to_dict()

def get_all_products():
    products = Product.get_all()
    return [product.to_dict() for product in products]

def get_product(product_id):
    product = Product.find_by_id(product_id)
    return product.to_dict() if product else None

def update_product(product_id, data):
    product = Product.find_by_id(product_id)
    if product:
        product.code = data.get('Code', product.code)
        product.name = data.get('Name', product.name)
        product.description = data.get('Description', product.description)
        product.category = data.get('Category', product.category)
        product.unit = data.get('Unit', product.unit)
        product.minimum_stock = data.get('Minimum_Stock', product.minimum_stock)
        product.current_stock = data.get('Current_Stock', product.current_stock)
        product.price = data.get('Price', product.price)
        product.barcode = data.get('Barcode', product.barcode)
        product.brand = data.get('Brand', product.brand)
        product.cost_price = data.get('CostPrice', product.cost_price)
        product.maximum_stock = data.get('Maximum_Stock', product.maximum_stock)
        product.tax_rate = data.get('TaxRate', product.tax_rate)
        product.supplier = data.get('Supplier', product.supplier)
        product.location = data.get('Location', product.location)
        product.update()
        return product.to_dict()
    return None

def delete_product(product_id):
    return Product.delete(product_id)