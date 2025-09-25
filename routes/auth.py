import datetime
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
import jwt
from config import Config
from services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)

# ----------------- API JSON para registro e inicio de sesión (HU1.1) -----------------
@auth_bp.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")
    nombre = data.get("nombre")
    rol = data.get("rol", "usuario")  # por defecto "usuario"

    if not email or not password or not nombre:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    result, status = AuthService.register(nombre, email, password, rol)
    return jsonify(result), status

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email == "admin@test.com" and password == "1234":
            return redirect(url_for("users.listar_usuarios"))
        else:
            flash("Credenciales inválidas", "error")

    return render_template("auth/login.html")


# Ruta API (para clientes JSON)
@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Correo y contraseña son obligatorios"}), 400

    user = AuthService.authenticate_user(email, password)
    if not user:
        return jsonify({"error": "Credenciales inválidas"}), 401

    payload = {
        "user_id": user["id"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")

    return jsonify({"message": "Inicio de sesión exitoso", "token": token})