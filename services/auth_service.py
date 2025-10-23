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
from utils.email_helper import send_email
from utils.audit_helper import log_event
import re
import dns.resolver
from email_validator import validate_email, EmailNotValidError

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
def register(nombre, email, password, rol="usuario"):
    try:
        # Validar datos antes de registrar
        is_valid, errors = AuthService.validate_user_data(nombre, email, password)
        if not is_valid:
            return {"error": "Errores de validación", "details": errors}, 400

        # Verificar si el email ya está registrado
        if AuthService.is_email_already_registered(email):
            return {"error": "El email ya está registrado"}, 400

        # Si todo está bien, crear el usuario
        user_id = User.create_user(nombre, email, password, rol)
        log_event("REGISTER", email, "SUCCESS", f"Usuario creado: {nombre}")
        
        return {
            "message": "Usuario registrado exitosamente",
            "user_id": user_id
        }, 201

    except psycopg2.IntegrityError as e:
        log_event("REGISTER", email, "ERROR", f"Error de integridad: {str(e)}")
        return {"error": "Error en los datos proporcionados"}, 400
    except Exception as e:
        log_event("REGISTER", email, "ERROR", str(e))
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
            except:
                location_info = {"error": "Could not parse location data"}
                raise

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

    payload = {
        "user_id": user.id,
        "email": user.email,
        "rol": user.rol,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=AuthService.SESSION_DURATION_HOURS)
    }
    token = jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=AuthService.SESSION_DURATION_HOURS)

    session = UserSession(
        user_id=user.id,
        session_token=token,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        expires_at=expires_at,
        is_active=True,
        ip_address=ip_address,
        user_agent=user_agent,
        location_data=location_str,
        last_activity=datetime.datetime.now()
    )
    session.save()
    return token, expires_at, ip_address, location_data

@staticmethod
def login(email, password, client_info=None):
    start = time.time()
    try:
        # Verificar credenciales
        user = User.find_by_email(email)
        if not user or not user.check_password(password):
            log_event("LOGIN", email, "FAILED", "Credenciales inválidas")
            return {"error": "Credenciales inválidas"}, 401

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
                "nombre": user.nombre,
                "email": user.email,
                "rol": user.rol,
                "two_factor_enabled": user.two_factor_enabled
            },
            "session_info": {
                "ip_address": ip_address,
                "location": location_data,
                "login_time": datetime.datetime.now().isoformat(),
                "expires_at": expires_at.isoformat(),
                "session_duration_hours": AuthService.SESSION_DURATION_HOURS
            },
            "requires_2fa": user.two_factor_enabled
        }

        if user.two_factor_enabled:
            response_data.update({
                "message": "Se ha enviado un código de verificación a tu correo",
                "2fa_required": True
            })

        log_event("LOGIN", email, "SUCCESS", 
                 f"Latencia={time.time()-start:.3f}s, IP={ip_address}, Location={location_data.get('city', 'Unknown')}")
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
            time_remaining = session.expires_at - datetime.datetime.now()
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
                    except:
                        location_info = {"error": "Could not parse location data"}
                        raise
                
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

    # === NUEVOS MÉTODOS PARA DESARROLLO ===

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
                except:
                    location_info = {"error": "Could not parse location data"}
                    raise
            
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
                "time_remaining_minutes": int((session.expires_at - datetime.datetime.now()).total_seconds() / 60)
            }
            
            return session_data, "Sesión encontrada"
        except Exception as e:
            return None, f"Error: {str(e)}"

    # === MÉTODOS EXISTENTES ===

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

            # Simulación envío de correo
            result = send_email(user.email, "Recuperación de usuario", f"Tu nombre de usuario es: {user.nombre}")

            log_event("RECOVER_USER", email, "SUCCESS", f"Latencia={result['latency']}s")
            return {"message": "Nombre de usuario enviado correctamente"}, 200

        except Exception as e:
            log_event("RECOVER_USER", email, "ERROR", str(e))
            return {"error": str(e)}, 500

@staticmethod
def recover_password(email):
        try:
            user = User.find_by_email(email)
            if not user:
                return {"error": "Usuario no encontrado"}, 404

            # Generar token temporal
            token = secrets.token_urlsafe(16)
            expira_en = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)

            # Guardar token en BD
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
            send_email(user.email, "Recuperación de contraseña", f"Usa este enlace: {reset_link}")

            return {"message": "Enlace de recuperación enviado"}, 200

        except Exception as e:
            return {"error": str(e)}, 500

@staticmethod
def reset_password(token, new_password):
        # Implementar lógica de reset de contraseña
        return {"message": "Funcionalidad en desarrollo"}, 200

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
        except:
            return False
            raise

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
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
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
                # Validación más estricta (opcional, puedes comentar esto si no quieres verificar dominio)
                # is_valid, email_error = AuthService.validate_email_comprehensive(email)
                # if not is_valid:
                #     errors.append(f"Email inválido: {email_error}")
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

@staticmethod
def is_email_already_registered(email):
        """Verificar si el email ya está registrado"""
        return User.find_by_email(email) is not None