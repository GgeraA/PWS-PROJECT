from models.Forecast import DemandForecast

def get_forecast_data(period: str = 'week'):
    """Obtener datos de predicción de demanda"""
    forecast = DemandForecast()
    return forecast.calculate_demand_forecast(period)

def export_forecast():
    """Exportar predicción a CSV"""
    forecast = DemandForecast()
    return forecast.export_forecast_data()