import psycopg2
import secrets
import time
from config import DATABASE
from utils.email_helper import send_email
from utils.sms_helper import send_sms
from utils.audit_helper import log_event

class AuthService:

    @staticmethod
    def recover_user(email_or_phone):
        start = time.time()
        try:
            conn = psycopg2.connect(**DATABASE)
            cur = conn.cursor()
            cur.execute("SELECT username, email, telefono FROM usuarios WHERE email = %s OR telefono = %s",
                        (email_or_phone, email_or_phone))
            user = cur.fetchone()
            conn.close()

            if not user:
                log_event("RECOVER_USER", email_or_phone, "FAILED", "Usuario no encontrado")
                return {"error": "Usuario no encontrado"}, 404

            nombre_usuario, correo, telefono = user

            # Notificación por correo o SMS
            if "@" in email_or_phone:
                result = send_email(correo, "Recuperación de usuario", f"Tu nombre de usuario es: {nombre_usuario}")
            else:
                result = send_sms(telefono, f"Tu nombre de usuario es: {nombre_usuario}")

            log_event("RECOVER_USER", email_or_phone, "SUCCESS", f"Latencia={result['latency']}s")
            return {"message": "Nombre de usuario enviado correctamente."}, 200

        except Exception as e:
            log_event("RECOVER_USER", email_or_phone, "ERROR", str(e))
            return {"error": str(e)}, 500
        finally:
            print(f"[PERF] Tiempo de respuesta recover_user={round(time.time()-start,3)}s")

    @staticmethod
    def recover_password(email_or_phone):
        start = time.time()
        try:
            conn = psycopg2.connect(**DATABASE)
            cur = conn.cursor()
            cur.execute("SELECT email, telefono FROM usuarios WHERE email = %s OR telefono = %s",
                        (email_or_phone, email_or_phone))
            user = cur.fetchone()
            conn.close()

            if not user:
                log_event("RECOVER_PASS", email_or_phone, "FAILED", "Usuario no encontrado")
                return {"error": "Usuario no encontrado"}, 404

            correo, telefono = user

            # Generar token temporal
            token = secrets.token_urlsafe(16)
            reset_link = f"https://tuapp.com/reset-password/{token}"

            # Notificación
            if "@" in email_or_phone:
                result = send_email(correo, "Recuperación de contraseña", f"Usa este enlace temporal: {reset_link}")
            else:
                result = send_sms(telefono, f"Usa este código temporal: {token}")

            log_event("RECOVER_PASS", email_or_phone, "SUCCESS", f"Latencia={result['latency']}s")
            return {"message": "Enlace de recuperación enviado."}, 200

        except Exception as e:
            log_event("RECOVER_PASS", email_or_phone, "ERROR", str(e))
            return {"error": str(e)}, 500
        finally:
            print(f"[PERF] Tiempo de respuesta recover_password={round(time.time()-start,3)}s")
