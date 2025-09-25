from flask import Blueprint, render_template, request, redirect, url_for
from models.user import User

users_bp = Blueprint("users", __name__)

@users_bp.route("/")
def listar_usuarios():
    usuarios = User.get_all()
    return render_template("users/usuarios.html", usuarios=usuarios)

@users_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo_usuario():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]
        rol = request.form["rol"]

        user = User(nombre=nombre, email=email, password=password, rol=rol)
        user.save()
        return redirect(url_for("users.listar_usuarios"))

    return render_template("users/nuevo_usuario.html")