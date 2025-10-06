from flask_restx import Namespace, Resource, fields
from services.user_service import assign_user_role, get_users_with_roles

api = Namespace("roles", description="Gestión de roles de usuario")

role_assignment_model = api.model("RoleAssignment", {
    "user_id": fields.Integer(required=True, description="ID del usuario"),
    "role": fields.String(required=True, description="Nuevo rol")
})

@api.route("/assign")
class AssignRole(Resource):
    @api.expect(role_assignment_model)
    @api.response(200, "Rol asignado")
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
            api.abort(404, "Usuario no encontrado")

        return {"message": "Rol actualizado", "user_id": user_id, "role": new_role}, 200

@api.route("/users")
class UsersWithRoles(Resource):
    def get(self):
        """Listar todos los usuarios con sus roles (solo admin)"""
        users = get_users_with_roles()
        return {"users": users}, 200