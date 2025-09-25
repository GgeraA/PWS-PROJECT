import psycopg2
import secrets
import time
import jwt
import datetime
from config import Config
from utils.email_helper import send_email
from utils.sms_helper import send_sms
from utils.audit_helper import log_event
from models.user import User
from passlib.hash import bcrypt


class AuthService:

    # ---------------- Recuperar usuario ----------------
    @staticmethod
    def recover_user(email):
        start = time.time()
        try:
            user = User.find_by_email(email)
            if not user:
                log_event("RECOVER_USER", email, "FAILED", "Usuario no encontrado")
                return {"error": "Usuario no encontrado"}, 404

            # Simulación envío de correo
            result = send_email(user.email, "Recuperación de usuario", f"Tu nombre de usuario es: {user.nombre}")

            log_event("RECOVER_USER", email, "SUCCESS", f"Latencia={result['latency']}s")
            return {"message": "Nombre de usuario enviado correctamente."}, 200

        except Exception as e:
            log_event("RECOVER_USER", email, "ERROR", str(e))
            return {"error": str(e)}, 500
        finally:
            print(f"[PERF] Tiempo de respuesta recover_user={round(time.time()-start,3)}s")

    # ---------------- Recuperar contraseña ----------------
    @staticmethod
    def recover_password(email):
        start = time.time()
        try:
            user = User.find_by_email(email)
            if not user:
                log_event("RECOVER_PASS", email, "FAILED", "Usuario no encontrado")
                return {"error": "Usuario no encontrado"}, 404

            # Generar token temporal
            token = secrets.token_urlsafe(16)
            reset_link = f"https://tuapp.com/reset-password/{token}"

            # Simulación envío de correo
            result = send_email(user.email, "Recuperación de contraseña", f"Usa este enlace temporal: {reset_link}")

            log_event("RECOVER_PASS", email, "SUCCESS", f"Latencia={result['latency']}s")
            return {"message": "Enlace de recuperación enviado."}, 200

        except Exception as e:
            log_event("RECOVER_PASS", email, "ERROR", str(e))
            return {"error": str(e)}, 500
        finally:
            print(f"[PERF] Tiempo de respuesta recover_password={round(time.time()-start,3)}s")

    # ---------------- Registro ----------------
    @staticmethod
    def register(nombre, email, password, rol="usuario"):
        try:
            user_id = User.create_user(nombre, email, password, rol)
        except Exception as e:
            return {"error": str(e)}, 500

        payload = {
            "user_id": user_id,
            "email": email,
            "role": rol,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=Config.JWT_EXP_DELTA_SECONDS)
        }
        token = jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
        return {"message": "Usuario registrado", "token": token}, 201

    # ---------------- Login ----------------
    @staticmethod
    def login(email, password):
        user = User.find_by_email(email)
        if not user:
            return {"error": "Usuario no encontrado"}, 404

        if not bcrypt.verify(password, user.password):
            return {"error": "Contraseña incorrecta"}, 401

        payload = {
            "user_id": user.id,
            "email": user.email,
            "role": user.rol,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=Config.JWT_EXP_DELTA_SECONDS)
        }
        token = jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
        return {"message": "Inicio de sesión exitoso", "token": token}, 200