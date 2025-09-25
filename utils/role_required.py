from functools import wraps
from flask import request, jsonify, g
import jwt
from config import Config

def _unauthorized(msg="Token ausente o inválido"):
    return jsonify({"error": msg}), 401

def _forbidden(msg="Permisos insuficientes"):
    return jsonify({"error": msg}), 403

def require_role(allowed_roles):
    """
    Decorador para proteger rutas por role.
    allowed_roles: lista de roles permitidos, e.g. ['admin', 'usuario']
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", None)
            if not auth:
                return _unauthorized("Authorization header missing")

            parts = auth.split()
            if parts[0].lower() != "bearer" or len(parts) != 2:
                return _unauthorized("Authorization header debe ser 'Bearer <token>'")

            token = parts[1]
            try:
                payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return _unauthorized("Token expirado")
            except jwt.InvalidTokenError:
                return _unauthorized("Token inválido")

            # payload debe contener 'role' (o 'rol') según cómo generes el JWT
            role = payload.get("role") or payload.get("rol")
            if role is None:
                return _forbidden("Role no presente en token")

            if role not in allowed_roles:
                return _forbidden(f"Acceso denegado para role '{role}'")

            # guardar info del usuario en flask.g para su uso posterior
            g.current_user = payload
            return f(*args, **kwargs)
        return wrapper
    return decorator