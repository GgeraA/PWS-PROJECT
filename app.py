from flask import Flask
from routes.main import main_bp
from routes.auth import auth_bp
from routes.users import users_bp  # si tienes uno para usuarios

def create_app():
    app = Flask(__name__)
    app.secret_key = "supersecret"  # cámbialo por uno seguro

    # Registrar Blueprints
    app.register_blueprint(main_bp, url_prefix="/")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(users_bp, url_prefix="/usuarios")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
