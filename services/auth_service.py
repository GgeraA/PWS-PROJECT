import email
import secrets
import time
import jwt
import datetime
import psycopg2
import requests
import json
from flask import request
from config import Config
from models.user import User
from models.user_session import UserSession
from werkzeug.security import check_password_hash
from flask_mail import Message
from utils.email_helper import send_email
from utils.audit_helper import log_event
import re
import dns.resolver
from email_validator import validate_email, EmailNotValidError

NOUSER = "Credenciales inválidas o Usuario No encontrado"

class AuthService:

    # Configuración de sesiones
    SESSION_DURATION_HOURS = 1  # Duración de la sesión en una hora
    ALLOW_MULTIPLE_SESSIONS = False  # Permitir múltiples sesiones

    @staticmethod
    def get_client_info():
        """Obtener información del cliente automáticamente"""
        if request.headers.get('X-Forwarded-For'):
            ip_address = request.headers.get('X-Forwarded-For').split(',')[0]
        elif request.headers.get('X-Real-IP'):
            ip_address = request.headers.get('X-Real-IP')
        else:
            ip_address = request.remote_addr

        user_agent = request.headers.get('User-Agent', '')
        location_data = AuthService.get_location_from_ip(ip_address)

        return {
            'ip_address': ip_address,
            'user_agent': user_agent,
            'location_data': location_data
        }

    @staticmethod
    def get_location_from_ip(ip_address):
        """Obtener ubicación geográfica basada en IP"""
        try:
            if ip_address in ['127.0.0.1', 'localhost', '::1']:
                return {
                    "ip": ip_address,
                    "city": "Localhost",
                    "region": "Local Network",
                    "country": "Local",
                    "loc": "0,0",
                    "timezone": "UTC"
                }

            response = requests.get(f'https://ipinfo.io/{ip_address}/json', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "ip": data.get('ip', ip_address),
                    "city": data.get('city', 'Unknown'),
                    "region": data.get('region', 'Unknown'),
                    "country": data.get('country', 'Unknown'),
                    "loc": data.get('loc', '0,0'),
                    "timezone": data.get('timezone', 'UTC'),
                    "org": data.get('org', 'Unknown')
                }
        except Exception as e:
            log_event("GEOLOCATION", ip_address, "ERROR", f"Falló geolocalización: {str(e)}")

        return {
            "ip": ip_address,
            "city": "Unknown",
            "region": "Unknown",
            "country": "Unknown",
            "loc": "0,0",
            "timezone": "UTC"
        }

    @staticmethod
    def is_email_already_registered(email):
        """Helper: comprobar si un email ya existe en users"""
        try:
            existing = User.find_by_email(email)
            return existing is not None
        except Exception:
            return False

    @staticmethod
    def register(nombre, email, password, rol="usuario"):
        try:
            # Validar datos antes de registrar
            is_valid, errors = AuthService.validate_user_data(nombre, email, password)
            if not is_valid:
                return {"error": "Errores de validación", "details": errors}, 400

            # Verificar si el email ya está registrado
            if AuthService.is_email_already_registered(email):
                return {"error": "El email ya está registrado"}, 400

            # Validaciones 
            if not all([nombre, email, password]):
                return {"error": "Todos los campos son requeridos"}, 400

            # Crear el usuario
            user_id = User.create_user(nombre, email, password, rol)
            log_event("REGISTER", email, "SUCCESS", f"Usuario creado: {nombre}")
            log_event("REGISTER", "SYSTEM", "SUCCESS", f"Usuario registrado: {email}")

            return {
                "message": "Usuario registrado exitosamente",
                "user_id": user_id,
                "email": email
            }, 201

        except Exception as e:
            log_event("REGISTER", "SYSTEM", "ERROR", f"Error: {str(e)}")
            return {"error": "Error interno del servidor"}, 500

    @staticmethod
    def _check_active_sessions(user_id):
        active_sessions = UserSession.find_active_by_user(user_id)
        if not active_sessions or AuthService.ALLOW_MULTIPLE_SESSIONS:
            return None

        session_info = []
        for session in active_sessions:
            location_info = {}
            if session.location_data:
                try:
                    location_info = json.loads(session.location_data)
                except Exception:
                    location_info = {"error": "Could not parse location data"}
                    # no hacemos raise para devolver info útil, pero si quieres puedes logear
            session_info.append({
                "session_id": session.id,
                "ip_address": session.ip_address,
                "location": location_info.get('city', 'Unknown'),
                "login_time": session.created_at.isoformat() if session.created_at else None,
                "last_activity": session.last_activity.isoformat() if session.last_activity else None
            })

        return {
            "error": "Ya tienes una sesión activa",
            "message": "Debes cerrar tu sesión actual antes de iniciar una nueva",
            "active_sessions": session_info,
            "session_count": len(active_sessions)
        }, 409

    @staticmethod
    def _create_session(user, client_info):
        ip_address = client_info.get('ip_address')
        user_agent = client_info.get('user_agent', '')[:500]
        location_data = client_info.get('location_data', {})
        location_str = json.dumps(location_data if location_data else {"error": "No location data"})

        # Obtener tiempo actual UTC
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        expiration_time = now_utc + datetime.timedelta(hours=AuthService.SESSION_DURATION_HOURS)
        
        # Crear payload con datetime objects, no timestamp
        payload = {
            "user_id": user.id,
            "email": user.email,
            "rol": getattr(user, 'rol', None),
            "exp": expiration_time,
            "iat": now_utc
        }
        
        # Generar token JWT - FORMA CORRECTA
        try:
            token = jwt.encode(
                payload,
                Config.SECRET_KEY,
                algorithm="HS256"
            )
            
            # Asegurar que token sea string (PyJWT 2.x devuelve string, versiones antiguas bytes)
            if isinstance(token, bytes):
                token = token.decode('utf-8')
                
        except Exception as e:
            log_event("JWT_GENERATION", user.email, "ERROR", f"Error generando token: {str(e)}")
            raise ValueError(f"Error generando token JWT: {str(e)}")

        expires_at = expiration_time

        session = UserSession(
            user_id=user.id,
            session_token=token,
            created_at=now_utc,
            expires_at=expires_at,
            is_active=True,
            ip_address=ip_address,
            user_agent=user_agent,
            location_data=location_str,
            last_activity=now_utc
        )
        
        try:
            session.save()
        except Exception as e:
            log_event("SESSION_SAVE", user.email, "ERROR", f"Error guardando sesión: {str(e)}")
            raise ValueError(f"Error guardando sesión: {str(e)}")
        
        return token, expires_at, ip_address, location_data
    @staticmethod
    def login(email, password, client_info=None):
        start = time.time()
        try:
            # Verificar credenciales
            user = User.find_by_email(email)
            if not user or not user.check_password(password):
                log_event("LOGIN", email, "FAILED", "Credenciales inválidas o Usuario No encontrado")
                return {"error": "Credenciales inválidas"}, 401

            print(f"🔍 LOGIN - Verificando sesiones activas para usuario {user.id}")
            active_sessions = UserSession.find_active_by_user(user.id)
            print(f"🔍 LOGIN - Sesiones activas encontradas: {len(active_sessions)}")

            # Verificar sesiones activas
            session_check = AuthService._check_active_sessions(user.id)
            if session_check:
                return session_check

            # Obtener información del cliente
            if not client_info:
                client_info = AuthService.get_client_info()

            # Crear sesión
            token, expires_at, ip_address, location_data = AuthService._create_session(user, client_info)

            response_data = {
                "message": "Inicio de sesión exitoso",
                "token": token,
                "user": {
                    "id": user.id,
                    "nombre": getattr(user, 'nombre', None),
                    "email": getattr(user, 'email', None),
                    "rol": getattr(user, 'rol', None),
                    "two_factor_enabled": getattr(user, 'two_factor_enabled', False)
                },
                "session_info": {
                    "ip_address": ip_address,
                    "location": location_data,
                    "login_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "expires_at": expires_at.isoformat(),
                    "session_duration_hours": AuthService.SESSION_DURATION_HOURS
                },
                "requires_2fa": getattr(user, 'two_factor_enabled', False)
            }

            if getattr(user, 'two_factor_enabled', False):
                response_data.update({
                    "message": "Se ha enviado un código de verificación a tu correo",
                    "2fa_required": True
                })

            loc_city = location_data.get('city', 'Unknown') if isinstance(location_data, dict) else 'Unknown'
            log_event("LOGIN", email, "SUCCESS",
                      f"Latencia={time.time()-start:.3f}s, IP={ip_address}, Location={loc_city}")
            return response_data, 200

        except Exception as e:
            log_event("LOGIN", email, "ERROR", str(e))
            return {"error": "Error interno del servidor"}, 500

    @staticmethod
    def verify_session(token):
        """Verificar si una sesión es válida y activa"""
        try:
            session = UserSession.find_by_token(token)
            if not session:
                return False, "Sesión no encontrada o expirada"

            # Verificar si la sesión está cerca de expirar (menos de 1 hora)
            time_remaining = session.expires_at - datetime.datetime.now(datetime.timezone.utc)
            if time_remaining.total_seconds() < 3600:  # 1 hora
                return True, "Sesión válida pero próxima a expirar"

            return True, "Sesión válida"
        except Exception as e:
            return False, f"Error verificando sesión: {str(e)}"

    @staticmethod
    def refresh_session(token):
        """Renovar una sesión existente"""
        try:
            success = UserSession.refresh_session(token, AuthService.SESSION_DURATION_HOURS)
            if success:
                return {"message": "Sesión renovada exitosamente"}, 200
            else:
                return {"error": "No se pudo renovar la sesión"}, 400
        except Exception as e:
            return {"error": f"Error renovando sesión: {str(e)}"}, 500

    @staticmethod
    def logout(session_token):
        try:
            success = UserSession.invalidate_session(session_token)
            if not success:
                log_event("LOGOUT", "SYSTEM", "ERROR", "Sesión no encontrada o ya cerrada")
                return {"error": "Sesión no encontrada o ya cerrada"}, 404

            log_event("LOGOUT", "SYSTEM", "SUCCESS", f"Sesión cerrada: {session_token[:10]}...")
            return {"message": "Sesión cerrada exitosamente"}, 200
        except Exception as e:
            log_event("LOGOUT", "SYSTEM", "ERROR", str(e))
            return {"error": str(e)}, 500

    @staticmethod
    def logout_all(user_id):
        """Cerrar todas las sesiones de un usuario"""
        try:
            UserSession.invalidate_all_user_sessions(user_id)
            log_event("LOGOUT_ALL", "SYSTEM", "SUCCESS", f"Todas las sesiones cerradas para usuario: {user_id}")
            return {"message": "Todas las sesiones han sido cerradas"}, 200
        except Exception as e:
            log_event("LOGOUT_ALL", "SYSTEM", "ERROR", str(e))
            return {"error": str(e)}, 500

    @staticmethod
    def get_active_sessions(user_id):
        """Obtener todas las sesiones activas de un usuario"""
        try:
            sessions = UserSession.find_active_by_user(user_id)
            session_list = []

            for session in sessions:
                location_info = {}
                if session.location_data:
                    try:
                        location_info = json.loads(session.location_data)
                    except Exception:
                        location_info = {"error": "Could not parse location data"}

                session_list.append({
                    "session_id": session.id,
                    "session_token": session.session_token[:20] + "...",  # No exponer token completo
                    "ip_address": session.ip_address,
                    "location": location_info,
                    "user_agent": session.user_agent,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                    "expires_at": session.expires_at.isoformat() if session.expires_at else None
                })

            return {"active_sessions": session_list, "count": len(session_list)}, 200
        except Exception as e:
            return {"error": str(e)}, 500

    @staticmethod
    def force_logout_all_sessions():
        """Forzar cierre de todas las sesiones (útil para desarrollo)"""
        try:
            conn = psycopg2.connect(**Config.DATABASE)
            cur = conn.cursor()
            cur.execute("""
                UPDATE user_sessions 
                SET is_active=false 
                WHERE is_active=true
            """)
            count = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            log_event("FORCE_LOGOUT_ALL", "SYSTEM", "SUCCESS", f"Sesiones cerradas: {count}")
            return count
        except Exception as e:
            log_event("FORCE_LOGOUT_ALL", "SYSTEM", "ERROR", str(e))
            return 0

    @staticmethod
    def get_all_active_sessions():
        """Obtener todas las sesiones activas en el sistema"""
        try:
            conn = psycopg2.connect(**Config.DATABASE)
            cur = conn.cursor()
            cur.execute("""
                SELECT us.id, us.user_id, u.nombre, u.email, us.ip_address, 
                       us.created_at, us.last_activity, us.expires_at, us.session_token
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                WHERE us.is_active=true AND us.expires_at > NOW()
                ORDER BY us.created_at DESC
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            sessions = []
            for row in rows:
                sessions.append({
                    "session_id": row[0],
                    "user_id": row[1],
                    "user_name": row[2],
                    "user_email": row[3],
                    "ip_address": row[4],
                    "created_at": row[5].isoformat() if row[5] else None,
                    "last_activity": row[6].isoformat() if row[6] else None,
                    "expires_at": row[7].isoformat() if row[7] else None,
                    "session_token_preview": f"{row[8][:20]}..." if row[8] else None
                })

            return sessions
        except Exception as e:
            log_event("GET_ALL_SESSIONS", "SYSTEM", "ERROR", str(e))
            return []

    @staticmethod
    def get_current_session_info(token):
        """Obtener información de la sesión actual"""
        try:
            session = UserSession.find_by_token(token)
            if not session:
                return None, "Sesión no encontrada o expirada"

            # Parsear location_data si existe
            location_info = {}
            if session.location_data:
                try:
                    location_info = json.loads(session.location_data)
                except Exception:
                    location_info = {"error": "Could not parse location data"}

            # calcular tiempo restante con timezone-aware
            time_remaining = session.expires_at - datetime.datetime.now(datetime.timezone.utc)
            minutes_remaining = int(time_remaining.total_seconds() / 60) if time_remaining.total_seconds() > 0 else 0

            session_data = {
                "session_id": session.id,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "location": location_info,
                "is_active": session.is_active,
                "time_remaining_minutes": minutes_remaining
            }

            return session_data, "Sesión encontrada"
        except Exception as e:
            return None, f"Error: {str(e)}"

    @staticmethod
    def verify_2fa(email, code):
        if code == "123456":  # Simulación
            return {"success": True, "message": "2FA verificado"}, 200
        else:
            return {"error": "Código 2FA inválido"}, 401

    @staticmethod
    def recover_user(email):
        try:
            user = User.find_by_email(email)
            if not user:
                return {"error": "Usuario no encontrado"}, 404

            print(f"📧 Enviando recuperación de usuario via Brevo a: {email}")

            subject = "Recuperación de Usuario - POS-ML"
            body = f"""
            Hola {user.nombre},

            Has solicitado recuperar tu nombre de usuario.

            Tu nombre de usuario es: {user.nombre}
        
            Si no solicitaste esta acción, por favor ignora este mensaje.

            Saludos,
            Equipo POS-ML
            """

            result = send_email(user.email, subject, body)

            print(f"📨 Resultado Brevo: {result}")
        
            if result.get("status") == "error":
                return {"error": f"No se pudo enviar el email: {result.get('error')}"}, 500

            log_event("RECOVER_USER", email, "SUCCESS", f"Brevo - Latencia: {result.get('latency', 0)}s")
            return {"message": "Nombre de usuario enviado correctamente a tu email"}, 200

        except Exception as e:
            log_event("RECOVER_USER", email, "ERROR", str(e))
            return {"error": "Error interno del servidor"}, 500

    @staticmethod
    def recover_password(email):
        """Recuperar contraseña usando Resend API - VERSIÓN CORREGIDA"""
        try:
            print(f"🔍 RECOVER_PASSWORD para: {email}")
            
            # 1. Buscar usuario
            user = User.find_by_email(email)
            if not user:
                # Por seguridad, no revelar si el email existe o no
                print(f"⚠️ Email no encontrado (por seguridad): {email}")
                return {"message": "Si el email existe, se enviarán instrucciones"}, 200
            
            print(f"✅ Usuario encontrado: {user.nombre}")
            
            # 2. Generar token seguro
            token = secrets.token_urlsafe(64)
            print(f"🔑 Token generado (primeros 10 chars): {token[:10]}...")
            
            # 3. Guardar en BD con expiración
            expira_en = datetime.datetime.now() + datetime.timedelta(minutes=30)
            
            conn = psycopg2.connect(**Config.DATABASE)
            cur = conn.cursor()
            
            # Primero, limpiar tokens previos para este email
            cur.execute("DELETE FROM password_resets WHERE email = %s", (email,))
            
            # Insertar nuevo token (SIN created_at - porque tu tabla no lo tiene)
            cur.execute(
                """INSERT INTO password_resets (email, token, expira_en) 
                VALUES (%s, %s, %s)""",
                (email, token, expira_en)
            )
            
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"✅ Token guardado en BD exitosamente")
            
            # 4. Crear enlace de reset
            # IMPORTANTE: Cambia esto a tu dominio real
            frontend_url = os.getenv('FRONTEND_URL', 'https://pos-frontend-13ys.onrender.com')
            reset_link = f"{frontend_url}/reset-password?token={token}"
            
            # 5. Preparar contenido del email
            subject = "🔐 Recuperación de Contraseña - POS-ML"
            
            # Versión texto plano (más simple)
            text_content = f"""
            Recuperación de Contraseña - POS-ML
            
            Hola {user.nombre},
            
            Has solicitado recuperar tu contraseña en POS-ML System.
            
            ⚡ Usa este enlace para restablecer tu contraseña:
            {reset_link}
            
            ⏰ Este enlace expirará en 30 minutos.
            
            ⚠️ Si no solicitaste este cambio, por favor ignora este mensaje.
            
            Saludos,
            Equipo POS-ML
            """
            
            # 6. Enviar email usando Resend
            from utils.email_resend import send_email_resend
            
            result = send_email_resend(
                to_email=email,
                subject=subject,
                body=text_content
            )
            
            if result.get("status") == "success":
                print(f"✅ Email enviado exitosamente con Resend")
                log_event("RECOVER_PASSWORD", email, "SUCCESS", 
                        f"Resend ID: {result.get('id', 'N/A')}")
                
                return {
                    "message": "Enlace de recuperación enviado a tu correo electrónico",
                    "email_sent": True,
                    "provider": "resend"
                }, 200
            else:
                print(f"❌ Resend falló: {result.get('error')}")
                
                # Para desarrollo/testing, mostrar el enlace
                if os.getenv('FLASK_ENV') == 'development' or os.getenv('DEBUG') == 'True':
                    return {
                        "message": "En desarrollo: Usa este enlace para resetear",
                        "reset_link": reset_link,
                        "token": token,
                        "note": f"Error email: {result.get('error')}",
                        "email_sent": False
                    }, 200
                else:
                    # En producción, solo decir que se procesó
                    return {
                        "message": "Solicitud procesada. Si no recibes el email en unos minutos, contacta soporte."
                    }, 200
                
        except Exception as e:
            print(f"❌ ERROR en recover_password: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            log_event("RECOVER_PASSWORD", email, "ERROR", str(e))
            
            # Respuesta segura
            return {
                "message": "Solicitud procesada. Si no recibes el email, contacta soporte técnico."
            }, 200
 
    @staticmethod
    def reset_password(token, new_password):
        """Restablecer contraseña con token válido - VERSIÓN CORREGIDA"""
        try:
            conn = psycopg2.connect(**Config.DATABASE)
            cur = conn.cursor()
            
            # Buscar token válido y no expirado
            cur.execute("""
                SELECT email, expira_en 
                FROM password_resets 
                WHERE token = %s AND expira_en > NOW()
            """, (token,))
            
            row = cur.fetchone()
            if not row:
                cur.close()
                conn.close()
                return {"error": "Token inválido o expirado"}, 400

            email_db = row[0]
            
            # Validar fortaleza de nueva contraseña
            is_valid, password_error = AuthService.validate_password_strength(new_password)
            if not is_valid:
                cur.close()
                conn.close()
                return {"error": password_error}, 400

            # Buscar usuario
            user = User.find_by_email(email_db)
            if not user:
                cur.close()
                conn.close()
                return {"error": "Usuario no encontrado"}, 404

            # Actualizar contraseña
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(new_password)
            
            cur.execute("""
                UPDATE users 
                SET password = %s 
                WHERE email = %s
            """, (password_hash, email_db))
            
            # Eliminar token usado
            cur.execute("DELETE FROM password_resets WHERE token = %s", (token,))
            
            conn.commit()
            cur.close()
            conn.close()

            # Opcional: Enviar email de confirmación
            try:
                subject = "✅ Contraseña Actualizada - POS-ML"
                body = f"""
                Hola {user.nombre},
                
                Tu contraseña ha sido actualizada exitosamente.
                
                Si no realizaste esta acción, por favor contacta al administrador inmediatamente.
                
                Saludos,
                Equipo POS-ML
                """
                
                from utils.email_resend import send_email_resend
                send_email_resend(email_db, subject, body)
                
            except Exception as email_error:
                print(f"⚠️ No se pudo enviar email de confirmación: {email_error}")
                # No fallar el reset por error de email

            log_event("RESET_PASSWORD", email_db, "SUCCESS", "Contraseña restablecida exitosamente")
            return {"message": "Contraseña actualizada correctamente"}, 200
            
        except Exception as e:
            log_event("RESET_PASSWORD", "SYSTEM", "ERROR", str(e))
            return {"error": "Error interno del servidor"}, 500
        
    @staticmethod
    def _send_email_fallback(email, nombre, token):
        """Fallback si Brevo falla"""
        try:
            print(f"🔄 Intentando fallback para {email}")
            
            # Usar otro método simple
            reset_link = f"https://pos-frontend-13ys.onrender.com/reset-password?token={token}"
            message = f"Recuperación para {nombre}: {reset_link}"
            
            # Solo loggear (para desarrollo)
            print(f"📝 [FALLBACK] Email simulado para {email}")
            print(f"📝 [FALLBACK] Enlace: {reset_link}")
            
            return {"message": "Instrucciones enviadas (modo desarrollo)"}, 200
            
        except Exception as e:
            print(f"❌ Fallback también falló: {e}")
            return {"message": "Procesado. Contacta soporte si no recibes email."}, 200

   
    @staticmethod
    def reset_password(token, new_password):
        """Restablecer contraseña con token válido - Versión mejorada"""
        try:
            conn = psycopg2.connect(**Config.DATABASE)
            cur = conn.cursor()
        
            # Buscar token válido y no expirado
            cur.execute("""
                SELECT email, expira_en 
                FROM password_resets 
                WHERE token = %s AND expira_en > NOW()
            """, (token,))
        
            row = cur.fetchone()
            if not row:
                cur.close()
                conn.close()
                return {"error": "Token inválido o expirado"}, 400

            email_db, expira_en = row[0], row[1]
        
            # Validar fortaleza de nueva contraseña
            is_valid, password_error = AuthService.validate_password_strength(new_password)
            if not is_valid:
                cur.close()
                conn.close()
                return {"error": password_error}, 400

            # Buscar usuario
            user = User.find_by_email(email_db)
            if not user:
                cur.close()
                conn.close()
                return {"error": "Usuario no encontrado"}, 404

            # Actualizar contraseña - Diferentes enfoques:
        
            # Opción A: Si User tiene método update_password
            if hasattr(User, 'update_password'):
                success = User.update_password(email_db, new_password)
                if not success:
                    cur.close()
                    conn.close()
                    return {"error": "Error al actualizar contraseña"}, 500
                
            # Opción B: Actualizar directamente
            else:
                from werkzeug.security import generate_password_hash
                password_hash = generate_password_hash(new_password)
                cur.execute("""
                    UPDATE users 
                    SET password = %s, updated_at = NOW()
                    WHERE email = %s
                """, (password_hash, email_db))
        
            # Eliminar token usado
            cur.execute("DELETE FROM password_resets WHERE token = %s", (token,))
            conn.commit()
            cur.close()
            conn.close()

            # Enviar email de confirmación
            try:
                subject = "Contraseña Actualizada - POS-ML"
                body = f"""
                Hola {user.nombre},

                Tu contraseña ha sido actualizada exitosamente.

                Si no realizaste esta acción, por favor contacta al administrador inmediatamente.

                Saludos,
                Equipo POS-ML
                """
                send_email(email_db, subject, body)
            except Exception as email_error:
                print(f"⚠️ No se pudo enviar email de confirmación: {email_error}")
                # No fallar el reset por error de email

            log_event("RESET_PASSWORD", email_db, "SUCCESS", "Contraseña restablecida exitosamente")
            return {"message": "Contraseña actualizada correctamente"}, 200
        
        except Exception as e:
            log_event("RESET_PASSWORD", "SYSTEM", "ERROR", str(e))
            return {"error": "Error interno del servidor"}, 500

    # ----------------------------- Validaciones de Usuario y correo ------------------------------
    @staticmethod
    def validate_email_format(email):
        """Validar formato de email básico con regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_email_domain(email):
        """Validar dominio del email (verificar que el dominio existe)"""
        try:
            domain = email.split('@')[1]
            # Verificar registros MX del dominio
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except Exception:
            return False

    @staticmethod
    def validate_email_comprehensive(email):
        """Validación completa de email usando email-validator"""
        try:
            # Validar email con la librería email-validator
            validate_email(email)
            return True, "Email válido"
        except EmailNotValidError as e:
            return False, str(e)

    @staticmethod
    def validate_password_strength(password):
        """Validar fortaleza de la contraseña"""
        if password is None:
            return False, "La contraseña es requerida"

        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"

        # Verificar que tenga al menos una letra minúscula
        if not re.search(r'[a-z]', password):
            return False, "La contraseña debe tener al menos una letra minúscula"

        # Verificar que tenga al menos una letra mayúscula
        if not re.search(r'[A-Z]', password):
            return False, "La contraseña debe tener al menos una letra mayúscula"

        # Verificar que tenga al menos un número
        if not re.search(r'\d', password):
            return False, "La contraseña debe tener al menos un número"

        # Verificar que tenga al menos un carácter especial
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            return False, "La contraseña debe tener al menos un carácter especial (!@#$%^&* etc.)"

        # Verificar que no tenga espacios
        if ' ' in password:
            return False, "La contraseña no puede contener espacios"

        return True, "Contraseña válida"

    @staticmethod
    def validate_password_common(password):
        """Verificar que la contraseña no sea común"""
        common_passwords = [
            'password', '12345678', '123456789', 'qwerty', 'abc123',
            'password1', '1234567', '123456', 'admin', 'welcome'
        ]

        if password.lower() in common_passwords:
            return False, "La contraseña es demasiado común"

        return True, "Contraseña aceptable"

    @staticmethod
    def validate_user_data(nombre, email, password):
        """Validación completa de datos de usuario"""
        errors = []

        # Validar nombre
        if not nombre or len(nombre.strip()) < 2:
            errors.append("El nombre debe tener al menos 2 caracteres")
        elif len(nombre) > 50:
            errors.append("El nombre no puede tener más de 50 caracteres")

        # Validar email
        if not email:
            errors.append("El email es requerido")
        else:
            # Validación básica con regex
            if not AuthService.validate_email_format(email):
                errors.append("El formato del email no es válido")
            else:
                # opción: comprobar dominio (puede hacer slow si dominio no responde)
                try:
                    if not AuthService.validate_email_domain(email):
                        errors.append("El dominio del email no parece tener registros MX válidos")
                except Exception:
                    # ignorar fallo de DNS para no bloquear registro
                    pass

        # Validar contraseña
        if not password:
            errors.append("La contraseña es requerida")
        else:
            # Validar fortaleza
            is_strong, password_error = AuthService.validate_password_strength(password)
            if not is_strong:
                errors.append(password_error)

            # Validar que no sea común
            is_uncommon, common_error = AuthService.validate_password_common(password)
            if not is_uncommon:
                errors.append(common_error)

        return len(errors) == 0, errors
