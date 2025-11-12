from flask import Flask
from flask_restx import Api
from flask_cors import CORS  # 👈 importa esto
from config import Config
from datetime import datetime
import json

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Importar namespaces
from routes.suppliers import api as suppliers_ns
from routes.products import api as products_ns
from routes.sales import api as sales_ns
from routes.sale_details import api as sale_details_ns
from routes.movement import api as movements_ns
from routes.user import api as users_ns
from routes.auth import api as auth_ns
from routes.roles import api as roles_ns
from routes.dev import api as dev_ns

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.json_encoder = CustomJSONEncoder  

    # 🔹 Configuración COMPLETA de CORS
    CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

    api = Api(
        app,
        version="1.0",
        title="PWS Project API",
        description="API para el punto de venta en Flask con documentación automática",
        doc="/docs",
        authorizations={
            'Bearer Auth': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': 'Ingrese: Bearer <token>'
            }
        },
        security='Bearer Auth'
    )

    # Registrar Namespaces
    api.add_namespace(products_ns, path="/products")
    api.add_namespace(suppliers_ns, path="/suppliers")
    api.add_namespace(sales_ns, path="/sales")
    api.add_namespace(sale_details_ns, path="/sale-details")
    api.add_namespace(movements_ns, path="/movements")
    api.add_namespace(users_ns, path="/users")
    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(roles_ns, path="/roles")
    api.add_namespace(dev_ns, path="/dev")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
