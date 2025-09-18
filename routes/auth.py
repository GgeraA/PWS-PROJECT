from flask import Blueprint, render_template, request, redirect, url_for, flash

auth_bp = Blueprint("auth", __name__)

# Login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # TODO: validar contra la BD
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
