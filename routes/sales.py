# routes/sales.py
from flask_restx import Namespace, Resource, fields
from services.sale_service import create_sale, get_all_sales, get_sale, update_sale, delete_sale

api = Namespace("sales", description="Sales operations")

sale_model = api.model("Sale", {
    "Sale_ID": fields.Integer(readOnly=True, description="ID de la venta"),
    "Date": fields.String(description="Fecha de la venta"),
    "User_ID": fields.Integer(required=True, description="ID del usuario que hizo la venta"),
    "Total": fields.Float(description="Total de la venta")
})

@api.route("/")
class SalesList(Resource):
    @api.marshal_list_with(sale_model,mask=False)
    def get(self):
        """Listar todas las ventas"""
        return get_all_sales()

    @api.expect(sale_model)
    @api.marshal_with(sale_model, code=201)
    def post(self):
        """Crear una nueva venta"""
        return create_sale(api.payload), 201


@api.route("/<int:sale_id>")
@api.response(404, "Sale not found")
class SaleResource(Resource):
    @api.marshal_with(sale_model,mask=False)
    def get(self, sale_id):
        """Obtener una venta por ID"""
        sale = get_sale(sale_id)
        if not sale:
            api.abort(404, "Sale not found")
        return sale

    @api.expect(sale_model)
    def put(self, sale_id):
        """Actualizar una venta existente"""
        sale = update_sale(sale_id, api.payload)
        if not sale:
            api.abort(404, "Sale not found")
        return {"message": "Sale updated"}

    def delete(self, sale_id):
        """Eliminar una venta"""
        success = delete_sale(sale_id)
        if not success:
            api.abort(404, "Sale not found")
        return {"message": "Sale deleted"}
