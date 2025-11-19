import pytest
from models.Product import Product
from unittest.mock import Mock, patch

def test_create_product_instance():
    """Prueba creación de producto con parámetros REALES"""
    p = Product(
        code="LTP001", 
        name="Laptop", 
        description="High-end laptop",
        category="Electronics", 
        unit="pcs",
        minimum_stock=5,
        current_stock=10,
        price=500.0
    )
    assert p.code == "LTP001"
    assert p.name == "Laptop"
    assert p.price == 500.0
    assert p.category == "Electronics"

def test_create_product_minimal():
    """Prueba creación con mínimos parámetros"""
    p = Product(name="Mouse", price=500.0)
    assert p.name == "Mouse"
    assert p.price == 500.0
    assert p.current_stock == 0  # Valor por defecto

def test_get_all_products(mock_db_connect):
    """Prueba obtener todos los productos"""
    _, _, cur = mock_db_connect
    cur.fetchall.return_value = [
        (1, "C1", "Laptop", "High-end", "Electronics", "pcs", 1, 10, 500)
    ]
    products = Product.get_all()
    assert len(products) == 1
    assert products[0].name == "Laptop"
    assert products[0].product_id == 1

def test_find_by_id_found(mock_db_connect):
    """Prueba buscar producto por ID (encontrado)"""
    _, _, cur = mock_db_connect
    cur.fetchone.return_value = (1, "C1", "Laptop", "High-end", "Electronics", "pcs", 1, 10, 500)
    
    result = Product.find_by_id(1)
    assert result is not None
    assert result.name == "Laptop"
    assert result.code == "C1"

def test_find_by_id_not_found(mock_db_connect):
    """Prueba buscar producto por ID (no encontrado)"""
    _, _, cur = mock_db_connect
    cur.fetchone.return_value = None
    
    result = Product.find_by_id(999)
    assert result is None

def test_save_new_product(mock_db_connect):
    """Prueba guardar nuevo producto"""
    _, _, cur = mock_db_connect
    cur.fetchone.return_value = (123,)  # Simular ID generado
    
    product = Product(
        code="NEW001", 
        name="New Product", 
        price=1000.0
    )
    
    result_id = product.save()
    assert result_id == 123
    assert product.product_id == 123

def test_update_product(mock_db_connect):
    """Prueba actualizar producto existente"""
    _, _, _ = mock_db_connect
    
    product = Product(
        product_id=1,
        code="UPD001", 
        name="Updated Product", 
        price=2000.0
    )
    
    result_id = product.update()
    assert result_id == 1

def test_delete_product_success(mock_db_connect):
    """Prueba eliminar producto (éxito)"""
    _, _, cur = mock_db_connect
    cur.fetchone.return_value = (1,)  # Producto eliminado
    
    result = Product.delete(1)
    assert result is True

def test_delete_product_failure(mock_db_connect):
    """Prueba eliminar producto (fallo)"""
    _, _, cur = mock_db_connect
    cur.fetchone.return_value = None  # No se encontró producto
    
    result = Product.delete(999)
    assert result is False