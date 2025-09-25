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


@auth_bp.route("/recover-password", methods=["POST"])
def api_recover_password():
    try:
        data = request.get_json()
        if not data or "contact" not in data:
            return jsonify({"error": "Falta el campo 'contact'"}), 400

        contact = data.get("contact")
        result, status = AuthService.recover_password(contact)
        return jsonify(result), status

    except Exception as e:
        return jsonify({"error": str(e)}), 500