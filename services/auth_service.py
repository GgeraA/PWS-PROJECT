import psycopg2
import secrets
import time
from config import DATABASE
from utils.email_helper import send_email
from utils.sms_helper import send_sms
from utils.audit_helper import log_event

class AuthService:

    @staticmethod
    def recover_user(contact):
        start = time.time()
        try:
            conn = psycopg2.connect(**DATABASE)
            cur = conn.cursor()
            # Ajuste a la tabla 'users'
            cur.execute(
                "SELECT nombre, email FROM users WHERE email = %s",
                (contact,)
            )
            user = cur.fetchone()
            conn.close()

            if not user:
                log_event("RECOVER_USER", contact, "FAILED", "Usuario no encontrado")
                return {"error": "Usuario no encontrado"}, 404

            nombre_usuario, correo = user

            # Notificación por correo
            if "@" in contact:
                result = send_email(correo, "Recuperación de usuario", f"Tu nombre de usuario es: {nombre_usuario}")
                log_event("RECOVER_USER", contact, "SUCCESS", f"Latencia={result['latency']}s")
            else:
                # Si agregas teléfono en la DB, se podría enviar SMS
                return {"error": "SMS no implementado"}, 400

            return {"message": "Nombre de usuario enviado correctamente."}, 200

        except Exception as e:
            log_event("RECOVER_USER", contact, "ERROR", str(e))
            return {"error": str(e)}, 500
        finally:
            print(f"[PERF] Tiempo recover_user={round(time.time()-start,3)}s")

    @staticmethod
    def recover_password(contact):
        start = time.time()
        try:
            conn = psycopg2.connect(**DATABASE)
            cur = conn.cursor()
            cur.execute(
                "SELECT email FROM users WHERE email = %s",
                (contact,)
            )
            user = cur.fetchone()
            conn.close()

            if not user:
                log_event("RECOVER_PASS", contact, "FAILED", "Usuario no encontrado")
                return {"error": "Usuario no encontrado"}, 404

            correo = user[0]

            # Generar token temporal
            token = secrets.token_urlsafe(16)
            reset_link = f"https://tuapp.com/reset-password/{token}"

            # Notificación por correo
            result = send_email(correo, "Recuperación de contraseña", f"Usa este enlace temporal: {reset_link}")
            log_event("RECOVER_PASS", contact, "SUCCESS", f"Latencia={result['latency']}s")

            return {"message": "Enlace de recuperación enviado."}, 200

        except Exception as e:
            log_event("RECOVER_PASS", contact, "ERROR", str(e))
            return {"error": str(e)}, 500
        finally:
            print(f"[PERF] Tiempo recover_password={round(time.time()-start,3)}s")
