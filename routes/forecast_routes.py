from flask_restx import Namespace, Resource, fields
from services.forecast_service import get_forecast_data, export_forecast

api = Namespace("ml/forecast", description="Predicción de Demanda con ML")

# Modelos para Swagger
forecast_model = api.model("Forecast", {
    "products": fields.List(fields.Raw),
    "timeline": fields.List(fields.Raw),
    "seasonalPatterns": fields.List(fields.Raw),
    "recommendations": fields.List(fields.Raw),
    "accuracy": fields.Float
})

@api.route("/")
class Forecast(Resource):
    @api.marshal_with(forecast_model)
    def get(self):
        """Obtener predicción de demanda"""
        from flask import request
        period = request.args.get('period', 'week')
        return get_forecast_data(period)

@api.route("/export")
class ForecastExport(Resource):
    def get(self):
        """Exportar predicción a CSV"""
        csv_data = export_forecast()
        return {
            "csv": csv_data,
            "filename": f"prediccion_demanda_{datetime.now().strftime('%Y-%m-%d')}.csv"
        }, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=prediccion_demanda_{datetime.now().strftime("%Y-%m-%d")}.csv'
        }