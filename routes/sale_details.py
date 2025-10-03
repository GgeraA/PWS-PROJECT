# routes/sale_details.py
from flask_restx import Namespace, Resource, fields
from services.sale_detail_service import (
    create_sale_detail, get_all_sale_details, get_sale_detail, update_sale_detail, delete_sale_detail
)

api = Namespace("sale-details", description="Sale Details operations")

sale_detail_model = api.model("SaleDetail", {
    "Detail_ID": fields.Integer(readOnly=True, description="ID del detalle"),
    "Sale_ID": fields.Integer(required=True, description="ID de la venta"),
    "Product_ID": fields.Integer(required=True, description="ID del producto"),
    "Quantity": fields.Integer(required=True, description="Cantidad vendida"),
    "Price": fields.Float(required=True, description="Precio unitario"),
    "Subtotal": fields.Float(description="Subtotal (Quantity * Price)")
})

@api.route("/")
class SaleDetailList(Resource):
    @api.marshal_list_with(sale_detail_model)
    def get(self):
        """Listar todos los detalles de venta"""
        return get_all_sale_details()

    @api.expect(sale_detail_model)
    @api.marshal_with(sale_detail_model, code=201)
    def post(self):
        """Crear un nuevo detalle de venta"""
        return create_sale_detail(api.payload), 201


@api.route("/<int:detail_id>")
@api.response(404, "Sale Detail not found")
class SaleDetailResource(Resource):
    @api.marshal_with(sale_detail_model)
    def get(self, detail_id):
        """Obtener detalle de venta por ID"""
        detail = get_sale_detail(detail_id)
        if not detail:
            api.abort(404, "Sale Detail not found")
        return detail

    @api.expect(sale_detail_model)
    def put(self, detail_id):
        """Actualizar un detalle de venta"""
        detail = update_sale_detail(detail_id, api.payload)
        if not detail:
            api.abort(404, "Sale Detail not found")
        return {"message": "Sale detail updated"}

    def delete(self, detail_id):
        """Eliminar un detalle de venta"""
        success = delete_sale_detail(detail_id)
        if not success:
            api.abort(404, "Sale Detail not found")
        return {"message": "Sale detail deleted"}
