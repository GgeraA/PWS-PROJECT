from flask_restx import Namespace, Resource
from services.auth_service import AuthService
from models.user_session import UserSession

api = Namespace("dev", description="Endpoints de desarrollo (solo para testing)")

@api.route("/force-logout-all")
class ForceLogoutAll(Resource):
    def post(self):
        """⚠️ CERRAR TODAS LAS SESIONES ACTIVAS (Solo para desarrollo)"""
        try:
            count = AuthService.force_logout_all_sessions()
            return {
                "message": "Todas las sesiones activas han sido cerradas",
                "sessions_closed": count,
                "warning": "⚠️ ESTO ES SOLO PARA DESARROLLO"
            }, 200
        except Exception as e:
            return {"error": str(e)}, 500

@api.route("/active-sessions")
class ActiveSessions(Resource):
    def get(self):
        """Obtener todas las sesiones activas en el sistema"""
        try:
            sessions = AuthService.get_all_active_sessions()
            return {
                "active_sessions": sessions,
                "total_sessions": len(sessions),
                "message": "Use POST /dev/force-logout-all para cerrar todas estas sesiones"
            }, 200
        except Exception as e:
            return {"error": str(e)}, 500

@api.route("/close-session/<int:user_id>")
class CloseUserSessions(Resource):
    def post(self, user_id):
        """Cerrar todas las sesiones de un usuario específico"""
        try:
            UserSession.invalidate_all_user_sessions(user_id)
            return {
                "message": "Todas las sesiones del usuario {user_id} han sido cerradas"
            }, 200
        except Exception as e:
            return {"error": str(e)}, 500