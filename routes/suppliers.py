from flask_restx import Namespace, Resource, fields
from services.supplier_service import (
    get_all_suppliers,
    get_supplier,
    create_supplier,
    update_supplier,
    delete_supplier
)

SUPPLIER_NOT_FOUND = "Proveedor no encontrado"

api = Namespace("suppliers", description="Operaciones relacionadas con proveedores")

# Modelo actualizado para aceptar todos los campos del frontend
supplier_model = api.model("Supplier", {
    "supplier_id": fields.Integer(readonly=True, description="ID del proveedor"),
    "name": fields.String(required=True, description="Nombre del proveedor"),
    "phone": fields.String(required=True, description="Teléfono"),
    "contact": fields.String(required=True, description="Persona de contacto"),
    "email": fields.String(description="Correo electrónico"),
    "address": fields.String(description="Dirección")
})

@api.route("/")
class SupplierList(Resource):
    @api.marshal_list_with(supplier_model, mask=False)
    def get(self):
        """Obtener todos los proveedores"""
        return get_all_suppliers()

    @api.expect(supplier_model)
    @api.response(201, "Proveedor creado")
    @api.marshal_with(supplier_model, mask=False)
    def post(self):
        """Crear un nuevo proveedor"""
        data = api.payload
        return create_supplier(data), 201

@api.route("/<int:supplier_id>")
@api.param("supplier_id", "El ID del proveedor")
class Supplier(Resource):
    @api.marshal_with(supplier_model, mask=False)
    def get(self, supplier_id):
        """Obtener un proveedor por ID"""
        supplier = get_supplier(supplier_id)
        if not supplier:
            api.abort(404, SUPPLIER_NOT_FOUND)
        return supplier

    @api.expect(supplier_model)
    @api.marshal_with(supplier_model, mask=False)
    def put(self, supplier_id):
        """Actualizar un proveedor existente"""
        data = api.payload
        supplier = update_supplier(supplier_id, data)
        if not supplier:
            api.abort(404, SUPPLIER_NOT_FOUND)
        return supplier

    @api.response(204, "Proveedor eliminado")
    def delete(self, supplier_id):
        """Eliminar un proveedor"""
        success = delete_supplier(supplier_id)
        if not success:
            api.abort(404, SUPPLIER_NOT_FOUND)
        return "", 204