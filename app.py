import os
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

from flask_restx import Api
from flask_cors import CORS
from config import Config
from datetime import datetime
import json

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
    
from extensions import mail    

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.json_encoder = CustomJSONEncoder  

    # 🔹 Configuración de CORS para producción y desarrollo
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000", 
        "https://tu-frontend-en-render.onrender.com"  # ACTUALIZAR con tu URL real
    ]
    
    CORS(app, 
         origins=allowed_origins, 
         supports_credentials=True,
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

    # 👇 Inicializar Flask-Mail con la aplicación
    mail.init_app(app)

    # 🔥 INICIALIZACIÓN AUTOMÁTICA DE BASE DE DATOS (SOLO EN PRODUCCIÓN)
    if app.config['FLASK_ENV'] == 'production':
        with app.app_context():
            try:
                from database.setup import initialize_database
                if initialize_database():
                    print("🎉 Base de datos inicializada correctamente en producción")
                else:
                    print("⚠️ Advertencia: Hubo problemas con la inicialización de la base de datos")
            except Exception as e:
                print(f"❌ Error en inicialización de BD: {e}")

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

    # 🔹 IMPORTANTE: Importar namespaces DESPUÉS de crear api y app
    from routes.suppliers import api as suppliers_ns
    from routes.products import api as products_ns
    from routes.sales import api as sales_ns
    from routes.sale_details import api as sale_details_ns
    from routes.movement import api as movements_ns
    from routes.user import api as users_ns
    from routes.auth import api as auth_ns
    from routes.roles import api as roles_ns
    from routes.dev import api as dev_ns
    from routes.sales_report import api as sales_report_ns
    from routes.reports import api as reports_ns
    from routes.ml_routes import api as ml_ns
    from routes.forecast_routes import api as forecast_ns

    # Registrar Namespaces
    api.add_namespace(products_ns, path="/api/products")
    api.add_namespace(suppliers_ns, path="/api/suppliers")
    api.add_namespace(sales_ns, path="/api/sales")
    api.add_namespace(sale_details_ns, path="/api/sale-details")
    api.add_namespace(movements_ns, path="/api/movements")
    api.add_namespace(users_ns, path="/api/users")
    api.add_namespace(auth_ns, path="/api/auth")
    api.add_namespace(roles_ns, path="/api/roles")
    api.add_namespace(dev_ns, path="/api/dev")
    api.add_namespace(sales_report_ns, path="/api/sales-report")
    api.add_namespace(reports_ns, path="/api/reports")
    api.add_namespace(forecast_ns, path='/api/ml/forecast')
    api.add_namespace(ml_ns, path='/api/ml')

    # 🔥 HEALTH CHECK endpoint para Render
    @app.route('/health')
    def health_check():
        from database.setup import DatabaseSetup
        setup = DatabaseSetup()
        
        db_status = "healthy" if setup.check_database_connection() else "unhealthy"
        tables_status = "complete" if setup.verify_tables_structure() else "incomplete"
        
        return jsonify({
            'status': 'healthy',
            'service': 'pws-backend',
            'database': db_status,
            'tables': tables_status,
            'environment': app.config['FLASK_ENV'],
            'timestamp': datetime.now().isoformat()
        })

    # Endpoint para forzar reinicialización de BD (útil para debugging)
    @app.route('/api/admin/init-db', methods=['POST'])
    def init_db():
        try:
            from database.setup import initialize_database
            success = initialize_database()
            return jsonify({
                'success': success,
                'message': 'Base de datos inicializada correctamente' if success else 'Error inicializando base de datos'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500

    # Manejo de errores global
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint no encontrado'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Error interno del servidor'}), 500

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)