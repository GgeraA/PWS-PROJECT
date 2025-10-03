# app/routes/products.py
from flask_restx import Namespace, Resource, fields
from services.product_service import (
    create_product,
    get_all_products,
    get_product,
    update_product,
    delete_product
)

# 🔹 Definir namespace
api = Namespace("products", description="Operaciones relacionadas con productos")

# 🔹 Modelo para Swagger
product_model = api.model("Product", {
    "Product_ID": fields.Integer(readonly=True, description="ID del producto"),
    "Code": fields.String(required=True, description="Código único del producto"),
    "Name": fields.String(required=True, description="Nombre del producto"),
    "Description": fields.String(description="Descripción del producto"),
    "Category": fields.String(description="Categoría"),
    "Unit": fields.String(description="Unidad de medida"),
    "Minimum_Stock": fields.Integer(description="Stock mínimo"),
    "Current_Stock": fields.Integer(description="Stock actual"),
    "Price": fields.Float(required=True, description="Precio del producto")
})


# -------------------------
# Endpoints CRUD
# -------------------------

@api.route("/")
class ProductList(Resource):
    @api.marshal_list_with(product_model)
    def get(self):
        """Obtener todos los productos"""
        return get_all_products()

    @api.expect(product_model)
    @api.response(201, "Producto creado")
    def post(self):
        """Crear un nuevo producto"""
        data = api.payload
        return create_product(data), 201


@api.route("/<int:product_id>")
@api.param("product_id", "El ID del producto")
class Product(Resource):
    @api.marshal_with(product_model)
    def get(self, product_id):
        """Obtener un producto por ID"""
        product = get_product(product_id)
        if not product:
            api.abort(404, "Producto no encontrado")
        return product

    @api.expect(product_model)
    def put(self, product_id):
        """Actualizar un producto existente"""
        data = api.payload
        product = update_product(product_id, data)
        if not product:
            api.abort(404, "Producto no encontrado")
        return product

    @api.response(204, "Producto eliminado")
    def delete(self, product_id):
        """Eliminar un producto"""
        success = delete_product(product_id)
        if not success:
            api.abort(404, "Producto no encontrado")
        return "", 204