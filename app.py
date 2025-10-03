from flask import Flask
from flask_restx import Api
from config import Config



# Importar blueprints convertidos en namespaces RESTX
from routes.suppliers import api as suppliers_ns
from routes.products import api as products_ns
from routes.sales import api as sales_ns
from routes.sale_details import api as sale_details_ns4
from routes.movement_routes import api as movements_ns
#from routes.users import api as users_ns
#from routes.auth import api as auth_ns
#from routes.roles import api as roles_ns

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 🚀 Inicializar Flask-RESTX API
    api = Api(
        app,
        version="1.0",
        title="PWS Project API",
        description="API para el punto de venta en Flask con documentación automática",
        doc="/docs"  # Ruta donde estará Swagger UI
    )

    # 🔹 Registrar Namespaces
    api.add_namespace(products_ns, path="/products")
    api.add_namespace(suppliers_ns, path="/suppliers")
    api.add_namespace(sales_ns, path="/sales")
    api.add_namespace(sale_details_ns4, path="/sale-details")
    api.add_namespace(movements_ns, path="/movements")
    #api.add_namespace(users_ns, path="/users")
    #api.add_namespace(auth_ns, path="/auth")
    #api.add_namespace(roles_ns, path="/roles")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
