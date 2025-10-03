from flask_restx import Namespace, Resource, fields
from services.user_service import (
    register_user,
    login_user,
    get_all_users,
    get_user,
    update_user,
    delete_user
)

# 🔹 Definir namespace
api = Namespace("users", description="Operaciones relacionadas con usuarios")

# 🔹 Modelo para Swagger
user_model = api.model("User", {
    "id": fields.Integer(readonly=True, description="ID del usuario"),
    "nombre": fields.String(required=True, description="Nombre del usuario"),
    "email": fields.String(required=True, description="Correo electrónico"),
    "password": fields.String(required=True, description="Contraseña del usuario"),
    "rol": fields.String(description="Rol del usuario (ej. admin, user)"),
    "two_factor_enabled": fields.Boolean(description="Indica si 2FA está habilitado"),
    "two_factor_secret": fields.String(description="Secreto para 2FA")
})

login_model = api.model("Login", {
    "email": fields.String(required=True, description="Correo electrónico"),
    "password": fields.String(required=True, description="Contraseña")
})

# -------------------------
# Endpoints CRUD + Login
# -------------------------

@api.route("/")
class UserList(Resource):
    @api.marshal_list_with(user_model)
    def get(self):
        """Obtener todos los usuarios"""
        return get_all_users()

    @api.expect(user_model)
    @api.response(201, "Usuario registrado")
    def post(self):
        """Registrar un nuevo usuario"""
        data = api.payload
        user = register_user(data)
        if not user:
            api.abort(400, "El email ya está registrado")
        return user, 201


@api.route("/<int:user_id>")
@api.param("user_id", "El ID del usuario")
class User(Resource):
    @api.marshal_with(user_model)
    def get(self, user_id):
        """Obtener un usuario por ID"""
        user = get_user(user_id)
        if not user:
            api.abort(404, "Usuario no encontrado")
        return user

    @api.expect(user_model)
    def put(self, user_id):
        """Actualizar un usuario existente"""
        data = api.payload
        user = update_user(user_id, data)
        if not user:
            api.abort(404, "Usuario no encontrado")
        return user

    @api.response(204, "Usuario eliminado")
    def delete(self, user_id):
        """Eliminar un usuario"""
        success = delete_user(user_id)
        if not success:
            api.abort(404, "Usuario no encontrado")
        return "", 204


@api.route("/login")
class UserLogin(Resource):
    @api.expect(login_model)
    def post(self):
        """Iniciar sesión"""
        data = api.payload
        user = login_user(data["email"], data["password"])
        if not user:
            api.abort(401, "Credenciales inválidas")
        return {"message": "Login exitoso", "user": {
            "id": user.id,
            "nombre": user.nombre,
            "email": user.email,
            "rol": user.rol,
            "two_factor_enabled": user.two_factor_enabled
        }}
