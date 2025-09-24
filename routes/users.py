from flask import Blueprint, request, jsonify
from services.user_service import get_all_users, create_user

users_bp = Blueprint("users", __name__)

@users_bp.route("/", methods=["GET"])
def list_users():
    users = get_all_users()
    return jsonify(users), 200

@users_bp.route("/", methods=["POST"])
def add_user():
    data = request.json
    user = create_user(data)
    if user:
        return jsonify(user), 201
    return jsonify({"error": "No se pudo crear el usuario"}), 400