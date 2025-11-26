from flask_restx import Namespace, Resource, fields
from services.sale_service import get_sales_with_details, get_sales_by_filters

api = Namespace("sales-report", description="Sales report operations")

sales_report_model = api.model("SalesReport", {
    "id": fields.Integer(description="ID de la venta"),
    "product_id": fields.Integer(description="ID del producto"),
    "product_name": fields.String(description="Nombre del producto"),
    "quantity": fields.Integer(description="Cantidad vendida"),
    "unit_price": fields.Float(description="Precio unitario"),
    "total": fields.Float(description="Total de la venta"),
    "date": fields.String(description="Fecha de la venta"),
    "user_id": fields.Integer(description="ID del vendedor"),
    "seller_name": fields.String(description="Nombre del vendedor"),
    "payment_method": fields.String(description="Método de pago")
})

@api.route("/")
class SalesReportList(Resource):
    @api.marshal_list_with(sales_report_model, mask=False)
    def get(self):
        """Obtener reporte completo de ventas con detalles"""
        return get_sales_with_details()

@api.route("/filtered")
class SalesReportFiltered(Resource):
    @api.marshal_list_with(sales_report_model, mask=False)
    def get(self):
        """Obtener ventas filtradas por fecha y método de pago"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        payment_method = request.args.get('payment_method')
        
        return get_sales_by_filters(start_date, end_date, payment_method)