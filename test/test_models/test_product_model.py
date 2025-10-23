import pytest
from models.Product import Product
def test_create_product_instance():
    p = Product(name="Laptop", code="LTP001", price=15000)
    assert p.name == "Laptop"
    assert p.price == pytest.approx(15000.0)

def test_get_all_products(mock_db_connect):
    from models.Product import Product
    _, _, cur = mock_db_connect
    cur.fetchall.return_value = [
        (1, "C1", "Laptop", "High-end", "Electronics", "pcs", 1, 10, 15000)
    ]
    products = Product.get_all()
    assert len(products) == 1
    assert products[0].name == "Laptop"

def test_find_by_id(mock_db_connect):
    from models.Product import Product
    _, _, cur = mock_db_connect
    cur.fetchone.return_value = (1, "C1", "Laptop", "High-end", "Electronics", "pcs", 1, 10, 15000)
    result = Product.find_by_id(1)
    assert result.name == "Laptop"

def test_delete_product(mock_db_connect):
    from models.Product import Product
    _, _, cur = mock_db_connect
    cur.fetchone.return_value = [1]
    assert Product.delete(1) is True
