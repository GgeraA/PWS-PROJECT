from flask import Blueprint, request, jsonify
from utils.role_required import require_role
from models.user import User  

roles_bp = Blueprint("roles", __name__)

ALLOWED_ROLES = {"admin", "usuario", "visitante"}

@roles_bp.route("/assign", methods=["PUT"])
@require_role(["admin"])
def assign_role():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    new_role = data.get("role")

    if not user_id or not new_role:
        return jsonify({"error": "user_id y role son obligatorios"}), 400

    if new_role not in ALLOWED_ROLES:
        return jsonify({"error": f"Role inválido. Debe ser uno de {list(ALLOWED_ROLES)}"}), 400

    updated = User.set_role(user_id, new_role)
    if not updated:
        return jsonify({"error": "Usuario no encontrado"}), 404

    return jsonify({"message": "Role actualizado", "user_id": user_id, "role": new_role}), 200

@roles_bp.route("/users", methods=["GET"])
@require_role(["admin"])
def list_users_roles():
    users = User.get_all_with_roles()  # define este método en el modelo
    return jsonify({"users": users}), 200
