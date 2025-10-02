from flask import Flask
from flask_cors import CORS
from routes.main import main_bp
from routes.auth import auth_bp
from routes.users import users_bp
from config import Config
from flask_swagger_ui import get_swaggerui_blueprint
from routes.roles import roles_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Carga config desde config.py
    
    # Habilitar CORS
    CORS(app)
    
        # Swagger UI
    SWAGGER_URL = "/docs"
    API_URL = "/static/swagger.yaml"
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={"app_name": "PWS Project API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # Registrar Blueprints
    app.register_blueprint(main_bp, url_prefix="/")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(users_bp, url_prefix="/user")
    app.register_blueprint(roles_bp, url_prefix="/roles")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
