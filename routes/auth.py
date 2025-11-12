from flask_restx import Namespace, Resource, fields, reqparse
from flask import request
from services.auth_service import AuthService
import jwt
from config import Config
from models.user_session import UserSession

EMAIL_DESC = "Correo electrónico"

api = Namespace("auth", description="Endpoints de autenticación")

# ------------------ Constantes ------------------
EMAIL_DESC = "Correo electrónico"
PASSWORD_DESC = "Contraseña"

ERR_FORMAT_TOKEN = "Formato de token inválido. Use: Bearer <token>"
ERR_TOKEN_REQUIRED = "Token de autorización requerido"
ERR_TOKEN_INVALID = "Token inválido"
ERR_TOKEN_EXPIRED = "Token expirado"
ERR_USER_ID_REQUIRED = "user_id es requerido"
ERR_ADMIN_ONLY = "Solo los administradores pueden usar este endpoint"

# ------------------ Parser MEJORADO ------------------
auth_parser = reqparse.RequestParser()
auth_parser.add_argument(
    'Authorization', 
    location='headers', 
    required=True, 
    help='Token de autorización en formato: Bearer <token>'
)

# ------------------ Funciones helper ORIGINALES ------------------
def extract_token():
    """Extrae el token del header Authorization"""
    args = auth_parser.parse_args()
    auth_header = args.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return None, {"error": ERR_FORMAT_TOKEN}, 401
        
    token = auth_header.replace('Bearer ', '')
    return token, None, None

def decode_token(token):
    """Decodifica JWT y devuelve payload o error"""
    try:
        # 1. Primero verificar en BD si la sesión está activa
        session = UserSession.find_by_token(token)
        if not session:
            return None, {"error": "Sesión cerrada o expirada"}, 401
        
        # 2. Luego verificar firma JWT
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        return payload, None, None
        
    except jwt.ExpiredSignatureError:
        return None, {"error": ERR_TOKEN_EXPIRED}, 401
    except jwt.InvalidTokenError:
        return None, {"error": ERR_TOKEN_INVALID}, 401


def verify_token(token):
    """Verificar token JWT y sesión en BD"""
    try:
        print(f"🔧 Verificando token: {token[:20]}...")
        
        # 1. Primero verificar en BD si la sesión está activa
        session = UserSession.find_by_token(token)
        if not session:
            return None, {"error": "Sesión cerrada o expirada"}, 401
        
        # 2. Luego verificar firma JWT
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        return payload, None, None
        
    except jwt.ExpiredSignatureError:
        return None, {"error": ERR_TOKEN_EXPIRED}, 401
    except jwt.InvalidTokenError:
        return None, {"error": ERR_TOKEN_INVALID}, 401
    except Exception as e:
        print(f"❌ ERROR verificando token: {e}")
        return None, {"error": "Error de autenticación"}, 500

# ------------------ Modelos Swagger ------------------
login_model = api.model("Login", {
    "email": fields.String(required=True, description=EMAIL_DESC),
    "password": fields.String(required=True, description=PASSWORD_DESC)
})

register_model = api.model("Register", {
    "nombre": fields.String(required=True, description="Nombre completo"),
    "email": fields.String(required=True, description=EMAIL_DESC),
    "password": fields.String(required=True, description=PASSWORD_DESC),
    "rol": fields.String(description="Rol del usuario", default="usuario", enum=['admin', 'usuario', 'visitante'])
})

logout_all_model = api.model("LogoutAll", {
    "user_id": fields.Integer(required=True, description="ID del usuario")
})

verify_2fa_model = api.model("Verify2FA", {
    "email": fields.String(required=True, description=EMAIL_DESC),
    "code": fields.String(required=True, description="Código 2FA")
})

recover_user_model = api.model("RecoverUser", {
    "email": fields.String(required=True, description=EMAIL_DESC)
})

recover_password_model = api.model("RecoverPassword", {
    "email": fields.String(required=True, description=EMAIL_DESC)
})

reset_password_model = api.model("ResetPassword", {
    "token": fields.String(required=True, description="Token de reset"),
    "new_password": fields.String(required=True, description="Nueva contraseña")
})

# ------------------ Funciones helper ------------------
def extract_token():
    """Extrae el token del header Authorization - Versión segura"""
    try:
        # Obtener header directamente
        auth_header = request.headers.get('Authorization', '')
        print(f"🔧 EXTRACT_TOKEN - Header: {auth_header[:50]}...")
        
        if not auth_header.startswith('Bearer '):
            return None, {"error": "Formato de token inválido"}, 401
        
        token = auth_header.replace('Bearer ', '')
        return token, None, None
        
    except Exception as e:
        print(f"❌ EXTRACT_TOKEN ERROR: {e}")
        return None, {"error": "Error extrayendo token"}, 500

def decode_token(token):
    """Decodifica JWT y verifica en BD"""
    try:
        # 1. Primero verifica si la sesión está activa en BD
        session = UserSession.find_by_token(token)
        if not session:
            return None, {"error": "Sesión cerrada o expirada"}, 401
        
        # 2. Luego verifica la firma JWT
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        return payload, None, None
        
    except jwt.ExpiredSignatureError:
        return None, {"error": ERR_TOKEN_EXPIRED}, 401
    except jwt.InvalidTokenError:
        return None, {"error": ERR_TOKEN_INVALID}, 401

# ------------------ Decorador personalizado para autenticación ------------------
def token_required(f):
    """Decorador para endpoints que requieren autenticación"""
    def decorated(*args, **kwargs):
        token, error, status = get_token_from_headers()
        if error:
            return error, status
            
        payload, error, status = verify_token(token)
        if error:
            return error, status
            
        # Inyectar user_id en los kwargs
        kwargs['user_id'] = payload.get('user_id')
        kwargs['user_role'] = payload.get('rol')
        kwargs['token'] = token
        
        return f(*args, **kwargs)
    return decorated        

# ------------------ Endpoints ------------------

@api.route("/register")
class Register(Resource):
    @api.expect(register_model)
    @api.response(201, "Usuario registrado")
    @api.response(400, "Error en los datos")
    def post(self):
        """Registrar nuevo usuario"""
        data = api.payload
        result, status = AuthService.register(
            data.get('nombre'),
            data.get('email'),
            data.get('password'),
            data.get('rol', 'usuario')
        )
        return result, status

@api.route("/login")
class Login(Resource):
    @api.expect(login_model)
    @api.response(200, "Login exitoso")
    @api.response(401, "Credenciales inválidas")
    @api.response(409, "Sesión activa existente")
    def post(self):
        """Iniciar sesión"""
        data = api.payload
        client_info = AuthService.get_client_info()
        result, status = AuthService.login(
            data.get('email'),
            data.get('password'),
            client_info
        )
        return result, status

@api.route("/logout")
class Logout(Resource):
    @api.expect(auth_parser)
    @api.response(200, "Sesión cerrada")
    @api.response(401, "Token requerido")
    @api.response(404, "Sesión no encontrada")
    def post(self):
        """Cerrar sesión actual"""
        token, error, status = extract_token()
        if error: 
            return error, status
        result, status = AuthService.logout(token)
        return result, status

    def options(self):
        return {}, 200

@api.route("/logout-all")
class LogoutAll(Resource):
    @api.expect(auth_parser, logout_all_model)  # ← auth_parser aquí
    @api.response(200, "Todas las sesiones cerradas")
    @api.response(400, "Error en los datos")
    def post(self):
        """Cerrar todas las sesiones de un usuario (para admin)"""
        token, error, status = extract_token()
        if error:
            return error, status
        payload, error, status = decode_token(token)
        if error:
            return error, status
        if payload.get('rol') != 'admin':
            return {"error": ERR_ADMIN_ONLY}, 403

        data = api.payload
        user_id = data.get('user_id')
        if not user_id:
            return {"error": ERR_USER_ID_REQUIRED}, 400

        result, status = AuthService.logout_all(user_id)
        return result, status

@api.route("/sessions")
class UserSessions(Resource):
    @api.expect(auth_parser)  
    @api.response(200, "Sesiones obtenidas")
    @api.response(401, "No autorizado")
    def get(self):
        """Obtener sesiones activas del usuario actual"""
        token, error, status = extract_token()
        if error:
            return error, status
        payload, error, status = decode_token(token)
        if error:
            return error, status
        user_id = payload.get('user_id')
        if not user_id:
            return {"error": ERR_TOKEN_INVALID}, 401
        result, status = AuthService.get_active_sessions(user_id)
        return result, status

@api.route("/verify-session")
class VerifySession(Resource):
    @api.expect(auth_parser)  
    @api.response(200, "Sesión verificada")
    @api.response(401, "Sesión inválida")
    def get(self):
        """Verificar si la sesión actual es válida"""
        token, error, status = extract_token()
        if error:
            return error, status
        is_valid, message = AuthService.verify_session(token)
        return ({"valid": True, "message": message}, 200) if is_valid else ({"valid": False, "message": message}, 401)

@api.route("/refresh-session")
class RefreshSession(Resource):
    @api.expect(auth_parser)  
    @api.response(200, "Sesión renovada")
    @api.response(400, "No se pudo renovar")
    def post(self):
        """Renovar la sesión actual"""
        token, error, status = extract_token()
        if error:
            return error, status
        result, status = AuthService.refresh_session(token)
        return result, status

@api.route("/client-info")
class ClientInfo(Resource):
    def get(self):
        """Obtener información del cliente (sin necesidad de token)"""
        client_info = AuthService.get_client_info()
        return {
            "client_info": client_info,
            "instructions": {
                "problem_sessions": "Si tiene problemas con sesiones activas, use:",
                "step_1": "GET /dev/active-sessions - Para ver todas las sesiones activas",
                "step_2": "POST /dev/force-logout-all - Para cerrar TODAS las sesiones",
                "step_3": "POST /auth/login - Para iniciar sesión nuevamente"
            }
        }, 200

@api.route("/verify-2fa")
class Verify2FA(Resource):
    @api.expect(auth_parser)  
    @api.expect(verify_2fa_model)
    @api.response(200, "2FA verificado")
    @api.response(401, "Código inválido")
    def post(self):
        """Verificar código 2FA"""
        data = api.payload
        result, status = AuthService.verify_2fa(
            data.get('email'),
            data.get('code')
        )
        return result, status

@api.route("/recover-user")
class RecoverUser(Resource):
    @api.expect(recover_user_model)
    @api.response(200, "Usuario recuperado")
    @api.response(404, "Usuario no encontrado")
    def post(self):
        """Recuperar nombre de usuario"""
        data = api.payload
        result, status = AuthService.recover_user(data.get('email'))
        return result, status

@api.route("/recover-password")
class RecoverPassword(Resource):
    @api.expect(recover_password_model)
    @api.response(200, "Enlace enviado")
    @api.response(404, "Usuario no encontrado")
    def post(self):
        """Solicitar recuperación de contraseña"""
        data = api.payload
        result, status = AuthService.recover_password(data.get('email'))
        return result, status

@api.route("/reset-password")
class ResetPassword(Resource):
    @api.expect(reset_password_model)
    @api.response(200, "Contraseña actualizada")
    @api.response(400, "Token inválido o expirado")
    def post(self):
        """Resetear contraseña con token"""
        data = api.payload
        result, status = AuthService.reset_password(
            data.get('token'),
            data.get('new_password')
        )
        return result, status

@api.route("/logout-test")
class LogoutTest(Resource):
    def post(self):
        """Logout sin auth_parser - para testing"""
        try:
            auth_header = request.headers.get('Authorization', '')
            print(f"🔧 LogoutTest - Header: {auth_header[:50]}...")
            
            if not auth_header.startswith('Bearer '):
                return {"error": "Token requerido"}, 401
                
            token = auth_header.replace('Bearer ', '')
            result, status = AuthService.logout(token)
            return result, status
        except Exception as e:
            return {"error": str(e)}, 500
    
    def options(self):
        return {}, 200
