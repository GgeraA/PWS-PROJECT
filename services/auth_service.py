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
from datetime import datetime, timedelta
from models.user_session import UserSession


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
            print(f"[PERF] Tiempo recover_user={round(time.time()-start,3)}s")

    # ---------------- Recuperar contraseña ----------------
    @staticmethod
    def recover_password(email):
        start = time.time()
        try:
            user = User.find_by_email(email)
            if not user:
                log_event("RECOVER_PASS", email, "FAILED", "Usuario no encontrado")
                return {"error": "Usuario no encontrado"}, 404

            # Generar token temporal y caducidad (30 min)
            token = secrets.token_urlsafe(16)
            expira_en = datetime.utcnow() + timedelta(minutes=30)

            # Guardar token en la BD
            conn = psycopg2.connect(**Config.DATABASE)

            cur = conn.cursor()
            cur.execute(
                "INSERT INTO password_resets (email, token, expira_en) VALUES (%s, %s, %s)",
                (email, token, expira_en)
            )
            conn.commit()
            cur.close()
            conn.close()

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
    

    @staticmethod
    def reset_password(token, new_password):
        try:
            # Conexión segura con 'with', se cierra sola al salir del bloque
            with psycopg2.connect(**Config.DATABASE) as conn:
                with conn.cursor() as cur:

                    # Buscar token válido
                    cur.execute(
                        "SELECT email, expira_en FROM password_resets WHERE token=%s",
                        (token,)
                    )
                    row = cur.fetchone()

                    if not row:
                        return {"error": "Token inválido"}, 400

                    email, expira_en = row
                    if datetime.utcnow() > expira_en:
                        return {"error": "Token expirado"}, 400

                    # Hashear nueva contraseña (max 72 caracteres)
                    hashed = bcrypt.hash(new_password[:72])

                    # Actualizar contraseña en users
                    cur.execute(
                        "UPDATE users SET password=%s WHERE email=%s",
                        (hashed, email)
                    )

                    # Eliminar token para que no se reuse
                    cur.execute(
                        "DELETE FROM password_resets WHERE token=%s",
                        (token,)
                    )

                    conn.commit()

                    log_event("RESET_PASS", email, "SUCCESS", "Contraseña cambiada")
                    return {"message": "Contraseña actualizada exitosamente"}, 200

        except Exception as e:
            log_event("RESET_PASS", None, "ERROR", str(e))
            return {"error": str(e)}, 500

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
            return {"success": False, "message": "Usuario no encontrado"}, 404

        if not bcrypt.verify(password, user.password):
            return {"success": False, "message": "Contraseña incorrecta"}, 401

        # Revisar si ya existe sesión activa
        active_session = UserSession.query.filter_by(user_id=user.id, is_active=True).first()
        if active_session:
            return {
                "success": False,
                "message": "Ya existe una sesión activa para este usuario. ¿Desea cerrarla?"
            }, 409

        # Crear nueva sesión
        payload = {
            "user_id": user.id,
            "email": user.email,
            "role": user.rol,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=Config.JWT_EXP_DELTA_SECONDS)
        }
        
        token = jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")

        new_session = UserSession(
            user_id=user.id,
            session_token=token,
            created_at=datetime.datetime.utcnow(),
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(seconds=Config.JWT_EXP_DELTA_SECONDS),
            is_active=True
        )
        new_session.save()

        return {
            "success": True,
            "message": "Inicio de sesión exitoso",
            "token": token,
            "usuario": {
                "id": user.id,
                "nombre": user.nombre,
                "email": user.email,
                "rol": user.rol
            }
        }, 200
        
# ---------------- logout ---------------------
    @staticmethod
    def logout(session_token):
        session = UserSession.query.filter_by(session_token=session_token, is_active=True).first()
        if not session:
            return {"success": False, "message": "Sesión no encontrada o ya cerrada"}, 404

        session.is_active = False
        session.save()

        return {"success": True, "message": "Sesión cerrada correctamente"}, 200

