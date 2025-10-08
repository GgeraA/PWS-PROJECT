# app/routes/suppliers.py
from flask_restx import Namespace, Resource, fields
from services.supplier_service import (
    get_all_suppliers,
    get_supplier,
    create_supplier,
    update_supplier,
    delete_supplier
)

api = Namespace("suppliers", description="Operaciones relacionadas con proveedores")

# Modelo para Swagger
supplier_model = api.model("Supplier", {
    "Supplier_ID": fields.Integer(readonly=True, description="ID del proveedor"),
    "Name": fields.String(required=True, description="Nombre del proveedor"),
    "Phone": fields.String(description="Teléfono"),
    "Contact": fields.String(description="Persona de contacto")
})

@api.route("/")
class SupplierList(Resource):
    @api.marshal_list_with(supplier_model,mask=False)
    def get(self):
        """Obtener todos los proveedores"""
        return get_all_suppliers()

    @api.expect(supplier_model)
    @api.response(201, "Proveedor creado")
    def post(self):
        """Crear un nuevo proveedor"""
        data = api.payload
        return create_supplier(data), 201

@api.route("/<int:supplier_id>")
@api.param("supplier_id", "El ID del proveedor")
class Supplier(Resource):
    @api.marshal_with(supplier_model,mask=False)
    def get(self, supplier_id):
        """Obtener un proveedor por ID"""
        supplier = get_supplier(supplier_id)
        if not supplier:
            api.abort(404, "Proveedor no encontrado")
        return supplier

    @api.expect(supplier_model)
    def put(self, supplier_id):
        """Actualizar un proveedor existente"""
        data = api.payload
        supplier = update_supplier(supplier_id, data)
        if not supplier:
            api.abort(404, "Proveedor no encontrado")
        return supplier

    @api.response(204, "Proveedor eliminado")
    def delete(self, supplier_id):
        """Eliminar un proveedor"""
        success = delete_supplier(supplier_id)
        if not success:
            api.abort(404, "Proveedor no encontrado")
        return "", 204
