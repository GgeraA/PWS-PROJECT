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

    # 🔹 CONFIGURACIÓN MEJORADA DE CORS (ESTILO EXPRESS.JS)
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000", 
        "https://pos-frontend-13ys.onrender.com",
        # Agregar más orígenes para compatibilidad con dispositivos
        "http://localhost:5174",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        # Para desarrollo móvil
        "http://10.0.2.2:3000",  # Android emulator
        "http://localhost:19006", # React Native
    ]
    
    # Configuración completa de CORS similar a Express.js
    CORS(app, 
        origins=allowed_origins,
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Content-Type", 
            "Authorization", 
            "X-Requested-With", 
            "Accept",
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
            "ngrok-skip-browser-warning"  # Para bypass de ngrok
        ],
        expose_headers=[
            "Content-Type", 
            "Authorization",
            "Content-Length",
            "X-Requested-With",
            "ngrok-skip-browser-warning"
        ],
        max_age=600
    )

    # 👇 Middleware para bypass de advertencias (similar a Express)
    @app.after_request
    def after_request(response):
        # Bypass para ngrok y otras herramientas
        response.headers.add('ngrok-skip-browser-warning', 'true')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        
        # Headers adicionales para compatibilidad
        response.headers.add('X-Content-Type-Options', 'nosniff')
        response.headers.add('X-Frame-Options', 'DENY')
        response.headers.add('X-XSS-Protection', '1; mode=block')
        
        return response

    # 👇 Manejar preflight requests explícitamente
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({"status": "preflight"})
            response.headers.add("Access-Control-Allow-Origin", 
                               request.headers.get("Origin", "*"))
            response.headers.add("Access-Control-Allow-Headers", 
                               "Content-Type, Authorization, X-Requested-With, Accept")
            response.headers.add("Access-Control-Allow-Methods", 
                               "GET, POST, PUT, DELETE, OPTIONS, PATCH")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            return response

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
    from routes.ml_routes import api as ml_nsRecomendation

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
    api.add_namespace(sales_report_ns, path="/sales-report")
    api.add_namespace(reports_ns, path="/reports")
    api.add_namespace(forecast_ns, path='/ml/forecast')
    #api.add_namespace(ml_ns, path='/ml')
    api.add_namespace(ml_nsRecomendation, path='/ml')

    # 🔥 HEALTH CHECK endpoint para Render (MEJORADO)
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
            'timestamp': datetime.now().isoformat(),
            'cors_enabled': True,
            'allowed_origins': allowed_origins
        })

    # 🔥 ENDPOINT RAIZ (similar a Express)
    @app.route('/')
    def root():
        return jsonify({
            'message': 'PWS Project API - Backend funcionando',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'health': '/health',
                'documentation': '/docs',
                'products': '/products',
                'sales': '/sales',
                'users': '/users',
                'auth': '/auth',
                'reports': '/reports'
            }
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

    # Manejo de errores global (MEJORADO)
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Endpoint no encontrado',
            'path': request.path,
            'method': request.method,
            'suggestion': 'Verifica que la URL sea correcta'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'error': 'Error interno' if app.config['ENV'] == 'production' else str(error)
        }), 500

    # Manejo de errores CORS
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'message': 'Método no permitido',
            'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']
        }), 405

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print('🚀 ===============================================')
    print('🚀 PWS Project API - Servidor Flask iniciado')
    print('🚀 ===============================================')
    print(f'📊 Puerto: {port}')
    print(f'🌐 URL: http://localhost:{port}')
    print(f'🔗 Health Check: http://localhost:{port}/health')
    print(f'📚 Documentación: http://localhost:{port}/docs')
    print(f'🌍 CORS habilitado para: {len(allowed_origins)} orígenes')
    print(f'📝 Entorno: {os.environ.get("FLASK_ENV", "development")}')
    print('🚀 ===============================================')
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)