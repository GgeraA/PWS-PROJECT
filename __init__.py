from flask import Flask
from .routes import main, usuarios, auth

def create_app():
    app = Flask(__name__)
    app.register_blueprint(main.bp)
    app.register_blueprint(usuarios.bp, url_prefix="/usuarios")
    app.register_blueprint(auth.bp, url_prefix="/auth")
    return app