from flask_restx import Namespace, Resource, fields, reqparse
from flask import request
from services.auth_service import AuthService
import jwt
from config import Config

api = Namespace("auth", description="Endpoints de autenticación")

# Parser para el header Authorization
auth_parser = reqparse.RequestParser()
auth_parser.add_argument('Authorization', location='headers', required=True, 
                        help='Token de autorización en formato: Bearer <token>')

# Modelos para Swagger
login_model = api.model("Login", {
    "email": fields.String(required=True, description="Correo electrónico"),
    "password": fields.String(required=True, description="Contraseña")
})

register_model = api.model("Register", {
    "nombre": fields.String(required=True, description="Nombre completo"),
    "email": fields.String(required=True, description="Correo electrónico"),
    "password": fields.String(required=True, description="Contraseña"),
    "rol": fields.String(description="Rol del usuario", default="usuario", enum=['admin', 'usuario', 'visitante'])
})

logout_all_model = api.model("LogoutAll", {
    "user_id": fields.Integer(required=True, description="ID del usuario")
})

verify_2fa_model = api.model("Verify2FA", {
    "email": fields.String(required=True, description="Correo electrónico"),
    "code": fields.String(required=True, description="Código 2FA")
})

recover_user_model = api.model("RecoverUser", {
    "email": fields.String(required=True, description="Correo electrónico")
})

recover_password_model = api.model("RecoverPassword", {
    "email": fields.String(required=True, description="Correo electrónico")
})

reset_password_model = api.model("ResetPassword", {
    "token": fields.String(required=True, description="Token de reset"),
    "new_password": fields.String(required=True, description="Nueva contraseña")
})

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
        args = auth_parser.parse_args()
        auth_header = args.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            # Si no hay token en los parámetros, intentar del header normal
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return {"error": "Formato de token inválido. Use: Bearer <token>"}, 401
            
        token = auth_header.replace('Bearer ', '')
        result, status = AuthService.logout(token)
        return result, status

@api.route("/logout-all")
class LogoutAll(Resource):
    @api.expect(auth_parser, logout_all_model)  # ✅ Usar parser + body
    @api.response(200, "Todas las sesiones cerradas")
    @api.response(400, "Error en los datos")
    def post(self):
        """Cerrar todas las sesiones de un usuario (para admin)"""
        args = auth_parser.parse_args()
        auth_header = args.get('Authorization')
        
        if not auth_header.startswith('Bearer '):
            return {"error": "Formato de token inválido. Use: Bearer <token>"}, 401
            
        # Verificar que el usuario sea admin
        token = auth_header.replace('Bearer ', '')
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            if payload.get('rol') != 'admin':
                return {"error": "Solo los administradores pueden usar este endpoint"}, 403
        except:
            return {"error": "Token inválido"}, 401
        
        data = api.payload
        user_id = data.get('user_id')
        if not user_id:
            return {"error": "user_id es requerido"}, 400
            
        result, status = AuthService.logout_all(user_id)
        return result, status

@api.route("/sessions")
class UserSessions(Resource):
    @api.expect(auth_parser)
    @api.response(200, "Sesiones obtenidas")
    @api.response(401, "No autorizado")
    def get(self):
        """Obtener sesiones activas del usuario actual"""
        args = auth_parser.parse_args()
        auth_header = args.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return {"error": "Token de autorización requerido"}, 401
            
        token = auth_header.replace('Bearer ', '')
        
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get('user_id')
            
            if not user_id:
                return {"error": "Token inválido"}, 401
                
            result, status = AuthService.get_active_sessions(user_id)
            return result, status
            
        except jwt.ExpiredSignatureError:
            return {"error": "Token expirado"}, 401
        except jwt.InvalidTokenError:
            return {"error": "Token inválido"}, 401

@api.route("/verify-session")
class VerifySession(Resource):
    @api.expect(auth_parser)  
    @api.response(200, "Sesión verificada")
    @api.response(401, "Sesión inválida")
    def get(self):
        """Verificar si la sesión actual es válida"""
        args = auth_parser.parse_args()
        auth_header = args.get('Authorization')
        
        if not auth_header.startswith('Bearer '):
            return {"error": "Formato de token inválido. Use: Bearer <token>"}, 401
            
        token = auth_header.replace('Bearer ', '')
        
        is_valid, message = AuthService.verify_session(token)
        if is_valid:
            return {"valid": True, "message": message}, 200
        else:
            return {"valid": False, "message": message}, 401

@api.route("/refresh-session")
class RefreshSession(Resource):
    @api.expect(auth_parser)  
    @api.response(200, "Sesión renovada")
    @api.response(400, "No se pudo renovar")
    def post(self):
        """Renovar la sesión actual"""
        args = auth_parser.parse_args()
        auth_header = args.get('Authorization')
        
        if not auth_header.startswith('Bearer '):
            return {"error": "Formato de token inválido. Use: Bearer <token>"}, 401
            
        token = auth_header.replace('Bearer ', '')
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