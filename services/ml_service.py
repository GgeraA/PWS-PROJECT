from models.recommendation import RecommendationSystem

def get_all_recommendations():
    """Obtener todas las recomendaciones"""
    recommender = RecommendationSystem()
    return recommender.get_all_recommendations()

def search_product_recommendations(query: str):
    """Buscar recomendaciones para un producto específico"""
    recommender = RecommendationSystem()
    return recommender.search_product_recommendations(query)

def create_bundle(items: list):
    """Crear un nuevo bundle (para implementar después)"""
    return {
        "message": "Bundle creado exitosamente",
        "bundle": {
            "id": 1,
            "name": "Bundle Personalizado",
            "items": items,
            "price": sum(len(item) * 1000 for item in items),  # Simulación
            "popularity": 75.0
        }
    }