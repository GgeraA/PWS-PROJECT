from models.movement import Movement

def test_create_movement_instance():
    m = Movement(type="entrada", product_id=1, quantity=5)
    assert m.type == "entrada"
    assert m.quantity == 5

def test_get_all_movements(mock_db_connect):
    _, _, cur = mock_db_connect
    cur.fetchall.return_value = [
        (1, "2024-01-01", "entrada", 1, 5, "ref1", 2, 3)
    ]
    movements = Movement.get_all()
    assert len(movements) == 1
    assert movements[0].type == "entrada"

def test_find_movement_by_id(mock_db_connect):
    _, _, cur = mock_db_connect
    cur.fetchone.return_value = (1, "2024-01-01", "salida", 1, 2, "ref2", 3, 4)
    result = Movement.find_by_id(1)
    assert result.type == "salida"

def test_delete_movement(mock_db_connect):
    _, _, cur = mock_db_connect
    cur.fetchone.return_value = [1]
    assert Movement.delete(1) is True
