from flask_restx import Namespace, Resource, fields
from services.sale_detail_service import (
    create_sale_detail, get_all_sale_details, get_sale_detail, update_sale_detail, delete_sale_detail
)

NOT_FOUND_MSG = "Sale Detail not found"

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
    @api.marshal_list_with(sale_detail_model,mask=False)
    def get(self):
        """Listar todos los detalles de venta"""
        return get_all_sale_details()

    @api.expect(sale_detail_model)
    @api.marshal_with(sale_detail_model, code=201)
    def post(self):
        """Crear un nuevo detalle de venta"""
        return create_sale_detail(api.payload), 201


@api.route("/<int:detail_id>")
@api.response(404, NOT_FOUND_MSG)
class SaleDetailResource(Resource):
    @api.marshal_with(sale_detail_model,mask=False)
    def get(self, detail_id):
        """Obtener detalle de venta por ID"""
        detail = get_sale_detail(detail_id)
        if not detail:
            api.abort(404, NOT_FOUND_MSG)
        return detail

    @api.expect(sale_detail_model)
    def put(self, detail_id):
        """Actualizar un detalle de venta"""
        detail = update_sale_detail(detail_id, api.payload)
        if not detail:
            api.abort(404, NOT_FOUND_MSG)
        return detil

    def delete(self, detail_id):
        """Eliminar un detalle de venta"""
        success = delete_sale_detail(detail_id)
        if not success:
            api.abort(404, NOT_FOUND_MSG)
        return detail
   
    @staticmethod
    def get_by_sale_id(sale_id):
        """Obtener todos los detalles de una venta específica"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            SELECT detail_id, sale_id, product_id, quantity, price, subtotal 
            FROM sale_details 
            WHERE sale_id = %s
        """, (sale_id,))
        rows = cur.fetchall()
        conn.close()
        return [SaleDetail(*row) for row in rows]