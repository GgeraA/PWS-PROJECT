from flask_restx import Namespace, Resource, fields
from services.ml_service import (
    get_all_recommendations,
    search_product_recommendations,
    create_bundle
)

# 🔹 Definir namespace
api = Namespace("ml", description="Sistema de Recomendaciones con Machine Learning")

# 🔹 Modelos para Swagger
product_recommendation_model = api.model("ProductRecommendation", {
    "id": fields.Integer(description="ID del producto"),
    "name": fields.String(description="Nombre del producto"),
    "category": fields.String(description="Categoría"),
    "price": fields.Float(description="Precio"),
    "confidence": fields.Float(description="Confianza de la recomendación"),
    "reason": fields.String(description="Razón de la recomendación"),
    "stock": fields.Integer(description="Stock disponible"),
    "code": fields.String(description="Código del producto")
})

bundle_model = api.model("Bundle", {
    "id": fields.Integer(description="ID del bundle"),
    "name": fields.String(description="Nombre del bundle"),
    "items": fields.List(fields.String, description="Productos incluidos"),
    "price": fields.Float(description="Precio del bundle"),
    "originalPrice": fields.Float(description="Precio original"),
    "popularity": fields.Float(description="Popularidad del bundle"),
    "discount": fields.Float(description="Descuento aplicado"),
    "savings": fields.Float(description="Ahorro")
})

cross_sell_model = api.model("CrossSell", {
    "id": fields.Integer(description="ID de la oportunidad"),
    "trigger": fields.String(description="Producto disparador"),
    "recommendation": fields.String(description="Recomendación"),
    "avgIncrease": fields.Float(description="Incremento promedio"),
    "conversions": fields.Integer(description="Conversiones"),
    "successRate": fields.Float(description="Tasa de éxito")
})

performance_metrics_model = api.model("PerformanceMetrics", {
    "acceptanceRate": fields.Float(description="Tasa de aceptación"),
    "additionalSales": fields.Float(description="Ventas adicionales"),
    "avgTicketIncrease": fields.Float(description="Incremento ticket promedio"),
    "mlAccuracy": fields.Float(description="Precisión del ML"),
    "totalConversions": fields.Integer(description="Total de conversiones"),
    "revenueIncrease": fields.Float(description="Incremento de ingresos")
})

recommendation_response_model = api.model("RecommendationResponse", {
    "productRecommendations": fields.List(fields.Nested(product_recommendation_model)),
    "bundleSuggestions": fields.List(fields.Nested(bundle_model)),
    "crossSellOpportunities": fields.List(fields.Nested(cross_sell_model)),
    "upsellItems": fields.List(fields.Raw),
    "trendingCombos": fields.List(fields.Raw),
    "performanceMetrics": fields.Nested(performance_metrics_model)
})

# -------------------------
# Endpoints de Recomendaciones
# -------------------------

@api.route("/recommendations")
class RecommendationList(Resource):
    @api.marshal_with(recommendation_response_model)
    def get(self):
        """Obtener todas las recomendaciones del sistema ML"""
        return get_all_recommendations()

@api.route("/recommendations/product")
class ProductRecommendation(Resource):
    def get(self):
        """Buscar recomendaciones para un producto específico"""
        from flask import request
        query = request.args.get('q', '')
        
        if len(query) < 2:
            return {"error": "La búsqueda debe tener al menos 2 caracteres"}, 400
        
        return search_product_recommendations(query)

@api.route("/recommendations/bundle")
class BundleCreation(Resource):
    def post(self):
        """Crear un nuevo bundle de productos"""
        from flask import request
        data = request.get_json()
        
        if not data or 'items' not in data:
            return {"error": "Se requiere la lista de items"}, 400
        
        return create_bundle(data['items'])

@api.route("/health")
class HealthCheck(Resource):
    def get(self):
        """Health check del sistema de recomendaciones"""
        return {
            "status": "healthy",
            "service": "ml-recommendation-system",
            "using_real_data": True
        }