from flask_restx import Namespace, Resource, fields
from services.user_service import (
    register_user,
    get_all_users,
    get_user,
    update_user,
    delete_user,
    assign_user_role,
    get_users_with_roles
)
from services.auth_service import AuthService

NOMBRE_DEL_USUARIO = "Nombre del usuario"
USUARIO_NO_ENCONTRADO = "Usuario no encontrado"
CORREO_ELECTRONICO = "Correo electrónico"
ROL_DEL_USUARIO = "Rol del usuario"
API_NAMESPACE = "users"
CONTRASENA = "Contraseña"
DOS_FA_HABILITADO = "2FA habilitado"
api = Namespace(API_NAMESPACE, description="Operaciones relacionadas con usuarios")

# Modelos para Swagger
user_model = api.model("User", {
    "id": fields.Integer(readonly=True, description="ID del usuario"),
    "nombre": fields.String(required=True, description=NOMBRE_DEL_USUARIO),
    "email": fields.String(required=True, description=CORREO_ELECTRONICO),
    "password": fields.String(required=True, description=CONTRASENA),
    "rol": fields.String(description=ROL_DEL_USUARIO, default="user"),
    "two_factor_enabled": fields.Boolean(description=DOS_FA_HABILITADO, default=False),
    "two_factor_secret": fields.String(description="Secreto 2FA"),
    "created_at": fields.DateTime(description="Fecha de creación"),
    "updated_at": fields.DateTime(description="Fecha de actualización")
})

user_register_model = api.model("UserRegister", {
    "nombre": fields.String(required=True, description=NOMBRE_DEL_USUARIO),
    "email": fields.String(required=True, description=CORREO_ELECTRONICO),
    "password": fields.String(required=True, description=CONTRASENA),
    "rol": fields.String(description=ROL_DEL_USUARIO, default="usuario", enum=['admin', 'usuario', 'visitante']),
    "two_factor_enabled": fields.Boolean(description=DOS_FA_HABILITADO, default=False)
})

user_update_model = api.model("UserUpdate", {
    "nombre": fields.String(description=NOMBRE_DEL_USUARIO),
    "email": fields.String(description=CORREO_ELECTRONICO),
    "password": fields.String(description=CONTRASENA),
    "rol": fields.String(description=ROL_DEL_USUARIO),
    "two_factor_enabled": fields.Boolean(description=DOS_FA_HABILITADO),
    "two_factor_secret": fields.String(description="Secreto 2FA")
})

role_assignment_model = api.model("RoleAssignment", {
    "user_id": fields.Integer(required=True, description="ID del usuario"),
    "role": fields.String(required=True, description="Nuevo rol")
})

@api.route("/")
class UserList(Resource):
    @api.marshal_list_with(user_model)
    def get(self):
        """Obtener todos los usuarios"""
        return get_all_users()

    @api.expect(user_register_model)
    @api.response(201, "Usuario registrado")
    @api.response(400, "El email ya está registrado")
    def post(self):
        """Registrar un nuevo usuario"""
        data = api.payload
        user = register_user(data)
        if not user:
            api.abort(400, "El email ya está registrado")
        return user, 201

@api.route("/<int:user_id>")
class UserDetail(Resource):
    @api.marshal_with(user_model)
    @api.response(404, USUARIO_NO_ENCONTRADO)
    def get(self, user_id):
        """Obtener un usuario por ID"""
        user = get_user(user_id)
        if not user:
            api.abort(404, USUARIO_NO_ENCONTRADO)
        return user

    @api.expect(user_update_model)
    @api.marshal_with(user_model)
    @api.response(404, USUARIO_NO_ENCONTRADO)
    def put(self, user_id):
        """Actualizar un usuario"""
        data = api.payload
        user = update_user(user_id, data)
        if not user:
            api.abort(404, USUARIO_NO_ENCONTRADO)
        return user

    @api.response(204, "Usuario eliminado")
    @api.response(404, USUARIO_NO_ENCONTRADO)
    def delete(self, user_id):
        """Eliminar un usuario"""
        success = delete_user(user_id)
        if not success:
            api.abort(404, USUARIO_NO_ENCONTRADO)
        return "", 204

@api.route("/roles/assign")
class RoleAssignment(Resource):
    @api.expect(role_assignment_model)
    @api.response(200, "Rol actualizado")
    @api.response(400, "Datos inválidos")
    @api.response(404, "Usuario no encontrado")
    def put(self):
        """Asignar rol a usuario (solo admin)"""
        data = api.payload
        user_id = data.get("user_id")
        new_role = data.get("role")

        if not user_id or not new_role:
            api.abort(400, "user_id y role son obligatorios")

        ALLOWED_ROLES = {"admin", "user", "viewer"}
        if new_role not in ALLOWED_ROLES:
            api.abort(400, f"Rol inválido. Debe ser uno de: {list(ALLOWED_ROLES)}")

        success = assign_user_role(user_id, new_role)
        if not success:
            api.abort(404, USUARIO_NO_ENCONTRADO)

        return {"message": "Rol actualizado", "user_id": user_id, "role": new_role}, 200

@api.route("/roles/list")
class UserRolesList(Resource):
    def get(self):
        """Listar todos los usuarios con sus roles (solo admin)"""
        users = get_users_with_roles()
        return {"users": users}, 200