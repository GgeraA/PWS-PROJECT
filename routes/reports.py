from flask_restx import Namespace, Resource, fields
from flask import request
from services.report_service import (
    get_sales_metrics, 
    get_sales_trend, 
    get_sales_by_category, 
    get_top_products
)

api = Namespace("reports", description="Sales reports operations")

# Modelos para la respuesta
metrics_model = api.model("Metrics", {
    "total_ventas": fields.Float(description="Ventas totales"),
    "total_transacciones": fields.Integer(description="Total de transacciones"),
    "ticket_promedio": fields.Float(description="Ticket promedio"),
    "total_productos": fields.Integer(description="Total de productos vendidos")
})

trend_model = api.model("Trend", {
    "fecha": fields.String(description="Fecha"),
    "ventas": fields.Float(description="Ventas del día"),
    "cantidad": fields.Integer(description="Cantidad de transacciones")
})

category_model = api.model("Category", {
    "nombre": fields.String(description="Nombre de la categoría"),
    "valor": fields.Float(description="Valor de ventas"),
    "cantidad": fields.Integer(description="Cantidad vendida")
})

product_model = api.model("TopProduct", {
    "nombre": fields.String(description="Nombre del producto"),
    "ventas": fields.Float(description="Ventas totales"),
    "cantidad": fields.Integer(description="Cantidad vendida")
})

@api.route("/metrics")
class SalesMetrics(Resource):
    @api.marshal_with(metrics_model, mask=False)
    def get(self):
        """Obtener métricas generales de ventas"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        return get_sales_metrics(start_date, end_date)

@api.route("/trend")
class SalesTrend(Resource):
    @api.marshal_list_with(trend_model, mask=False)
    def get(self):
        """Obtener tendencia de ventas"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        return get_sales_trend(start_date, end_date)

@api.route("/categories")
class SalesByCategory(Resource):
    @api.marshal_list_with(category_model, mask=False)
    def get(self):
        """Obtener ventas por categoría"""
        return get_sales_by_category()

@api.route("/top-products")
class TopProducts(Resource):
    @api.marshal_list_with(product_model, mask=False)
    def get(self):
        """Obtener productos más vendidos"""
        limit = request.args.get('limit', 5, type=int)
        return get_top_products(limit)