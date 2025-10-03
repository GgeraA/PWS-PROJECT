# services/movement_service.py
from models.movement import Movement

def get_all_movements():
    return Movement.get_all()

def get_movement(movement_id):
    return Movement.find_by_id(movement_id)

def create_movement(data):
    movement = Movement(
        Type=data.get("Type"),
        Product_ID=data.get("Product_ID"),
        Quantity=data.get("Quantity"),
        Reference=data.get("Reference"),
        Supplier_ID=data.get("Supplier_ID"),
        User_ID=data.get("User_ID")
    )
    movement.save()
    return movement

def update_movement(movement_id, data):
    movement = Movement.find_by_id(movement_id)
    if not movement:
        return None

    movement.Type = data.get("Type", movement.Type)
    movement.Product_ID = data.get("Product_ID", movement.Product_ID)
    movement.Quantity = data.get("Quantity", movement.Quantity)
    movement.Reference = data.get("Reference", movement.Reference)
    movement.Supplier_ID = data.get("Supplier_ID", movement.Supplier_ID)
    movement.User_ID = data.get("User_ID", movement.User_ID)

    movement.update()
    return movement

def delete_movement(movement_id):
    return Movement.delete(movement_id)
