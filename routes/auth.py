import datetime
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
import jwt
from config import Config
from werkzeug.security import check_password_hash
from models.user import User
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

        user = User.get_by_email(email)  # necesitas este método en tu modelo
        if user and check_password_hash(user.password, password):
            # login correcto: redirige o crea session/jwt, etc.
            return redirect(url_for("users.listar_usuarios"))
        else:
            flash("Credenciales inválidas", "error")

    return render_template("auth/login.html")


# Recuperar contraseña (HU1.3)
@auth_bp.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    if request.method == "POST":
        email = request.form["email"]

        # TODO: enviar token al correo
        flash(f"Se envió un enlace de recuperación a {email}", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/recuperar.html")


# Verificación OTP (HU1.4 - 2FA)
@auth_bp.route("/verificar-otp", methods=["GET", "POST"])
def verificar_otp():
    if request.method == "POST":
        codigo = request.form["codigo"]

        # TODO: validar OTP real (ejemplo: PyOTP o SMS)
        if codigo == "123456":  # simulado
            flash("Acceso concedido", "success")
            return redirect(url_for("users.listar_usuarios"))
        else:
            flash("Código inválido o expirado", "error")

    return render_template("auth/verificar_otp.html")

# ----------------- API JSON -----------------
# HU1.2 - Recuperar usuario
@auth_bp.route("/recover-user", methods=["POST"])
def api_recover_user():
    data = request.get_json()
    contact = data.get("contact")
    result, status = AuthService.recover_user(contact)
    return jsonify(result), status


# ---------------- Recuperar contraseña ----------------
@auth_bp.route("/recover-password", methods=["POST"])
def recover_password():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email requerido"}), 400

    response, status = AuthService.recover_password(email)
    return jsonify(response), status


# ---------------- Resetear contraseña ----------------
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    token = data.get("token")
    new_password = data.get("new_password")

    if not token or not new_password:
        return jsonify({"error": "Token y nueva contraseña requeridos"}), 400

    response, status = AuthService.reset_password(token, new_password)
    return jsonify(response), status