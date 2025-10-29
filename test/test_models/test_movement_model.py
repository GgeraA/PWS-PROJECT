import pytest
from models.movement import Movement
from datetime import datetime

def test_create_movement_instance():
    """Prueba creación de movimiento con parámetros REALES"""
    m = Movement(
        type="entrada",
        product_id=1,
        quantity=5,
        reference="REF001",
        supplier_id=2,
        user_id=3
    )
    assert m.type == "entrada"
    assert m.product_id == 1
    assert m.quantity == 5
    assert m.reference == "REF001"

def test_create_movement_minimal():
    """Prueba creación con mínimos parámetros"""
    m = Movement(type="salida", product_id=1, quantity=2)
    assert m.type == "salida"
    assert m.quantity == 2
    assert m.product_id == 1

def test_get_all_movements(mock_db_connect):
    """Prueba obtener todos los movimientos"""
    _, _, cur = mock_db_connect
    cur.fetchall.return_value = [
        (1, "2024-01-01", "entrada", 1, 5, "ref1", 2, 3)
    ]
    movements = Movement.get_all()
    assert len(movements) == 1
    assert movements[0].type == "entrada"
    assert movements[0].movement_id == 1

def test_find_by_id_found(mock_db_connect):
    """Prueba buscar movimiento por ID (encontrado)"""
    _, _, cur = mock_db_connect
    cur.fetchone.return_value = (1, "2024-01-01", "salida", 1, 2, "ref2", 3, 4)
    
    result = Movement.find_by_id(1)
    assert result is not None
    assert result.type == "salida"
    assert result.quantity == 2

def test_find_by_id_not_found(mock_db_connect):
    """Prueba buscar movimiento por ID (no encontrado)"""
    _, _, cur = mock_db_connect
    cur.fetchone.return_value = None
    
    result = Movement.find_by_id(999)
    assert result is None

def test_save_new_movement(mock_db_connect):
    """Prueba guardar nuevo movimiento"""
    conn, _, cur = mock_db_connect
    cur.fetchone.return_value = [456]  # Simular ID generado
    
    movement = Movement(
        type="entrada",
        product_id=1,
        quantity=10,
        reference="TEST123"
    )
    
    result_id = movement.save()
    assert result_id == 456
    assert movement.movement_id == 456
    conn.commit.assert_called_once()

def test_update_movement(mock_db_connect):
    """Prueba actualizar movimiento existente"""
    conn, _, cur = mock_db_connect
    
    movement = Movement(
        movement_id=1,
        type="entrada",
        product_id=1,
        quantity=15,
        reference="UPDATED"
    )
    
    result_id = movement.update()
    assert result_id == 1
    conn.commit.assert_called_once()

def test_delete_movement_success(mock_db_connect):
    """Prueba eliminar movimiento (éxito)"""
    _, _, cur = mock_db_connect
    cur.fetchone.return_value = [1]  # Movimiento eliminado
    
    result = Movement.delete(1)
    assert result is True

def test_delete_movement_failure(mock_db_connect):
    """Prueba eliminar movimiento (fallo)"""
    _, _, cur = mock_db_connect
    cur.fetchone.return_value = None  # No se encontró movimiento
    
    result = Movement.delete(999)
    assert result is False