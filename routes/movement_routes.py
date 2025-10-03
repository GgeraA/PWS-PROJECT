# routes/movements.py
from flask_restx import Namespace, Resource, fields
from flask import request
from services.movement_service import (
    get_all_movements, get_movement, create_movement,
    update_movement, delete_movement
)

api = Namespace("movements", description="Movements operations")

# Swagger model
movement_model = api.model("Movement", {
    "Movement_ID": fields.Integer(readonly=True, description="ID del movimiento"),
    "Date": fields.DateTime(description="Fecha del movimiento"),
    "Type": fields.String(required=True, description="Tipo: Entry o Exit"),
    "Product_ID": fields.Integer(required=True, description="Producto asociado"),
    "Quantity": fields.Integer(required=True, description="Cantidad del movimiento"),
    "Reference": fields.String(description="Referencia del movimiento"),
    "Supplier_ID": fields.Integer(description="Proveedor asociado"),
    "User_ID": fields.Integer(description="Usuario que hizo el movimiento"),
})

@api.route("/")
class MovementList(Resource):
    @api.marshal_list_with(movement_model)
    def get(self):
        """Listar todos los movimientos"""
        return get_all_movements()

    @api.expect(movement_model, validate=True)
    def post(self):
        """Crear un movimiento"""
        data = request.json
        movement = create_movement(data)
        return {"message": "Movimiento creado", "Movement_ID": movement.Movement_ID}, 201


@api.route("/<int:movement_id>")
@api.response(404, "Movimiento no encontrado")
class MovementResource(Resource):
    @api.marshal_with(movement_model)
    def get(self, movement_id):
        """Obtener un movimiento por ID"""
        movement = get_movement(movement_id)
        if not movement:
            api.abort(404, "Movimiento no encontrado")
        return movement

    @api.expect(movement_model, validate=True)
    def put(self, movement_id):
        """Actualizar un movimiento"""
        data = request.json
        movement = update_movement(movement_id, data)
        if not movement:
            api.abort(404, "Movimiento no encontrado")
        return {"message": "Movimiento actualizado"}

    def delete(self, movement_id):
        """Eliminar un movimiento"""
        success = delete_movement(movement_id)
        if not success:
            api.abort(404, "Movimiento no encontrado")
        return {"message": "Movimiento eliminado"}
