import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 🔥 CONFIGURACIÓN DINÁMICA PARA RENDER/PRODUCCIÓN
    @staticmethod
    def get_database_config():
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            
            parsed = urllib.parse.urlparse(database_url)
            
            return {
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path[1:],
                'user': parsed.username,
                'password': parsed.password
            }
        else:
            return {
                'database': 'seguridad',  
                'user': 'postgres', 
                'password': '1234', 
                'host': 'localhost', 
                'port': 5432 
            }
    
    # 🔥 AGREGAR PARA COMPATIBILIDAD CON CÓDIGO EXISTENTE
    DATABASE = get_database_config.__func__()
    
    # Seguridad
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key-for-development-only")
    JWT_EXP_DELTA_SECONDS = int(os.getenv("JWT_EXP_DELTA_SECONDS", 300))

    # 🔥🔧 CONFIGURACIÓN DE EMAIL ACTUALIZADA
    # ----------------------------------------
    # 1. MAILGUN (PRIMERA OPCIÓN - FUNCIONA EN RENDER)
    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "")
    MAILGUN_FROM_EMAIL = os.getenv("MAILGUN_FROM_EMAIL", "noreply@pos-ml.com")
    
    # 2. RESEND (SEGUNDA OPCIÓN)
    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    
    # 3. BREVO/SMTP (TERCERA OPCIÓN - solo desarrollo local)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp-relay.brevo.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "9c4c04001@smtp-brevo.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "respaldogg20@gmail.com")
    MAIL_DEBUG = False
    MAIL_SUPPRESS_SEND = False
    
    # URL del Frontend
    FRONTEND_URL = os.getenv("FRONTEND_URL", "https://pos-frontend-13ys.onrender.com")
    
    # Configuración de entorno
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # 🔥 MÉTODOS DE AYUDA PARA EMAIL
    @staticmethod
    def get_email_provider():
        """Determina qué proveedor de email usar basado en configuración"""
        if Config.MAILGUN_API_KEY and Config.MAILGUN_DOMAIN:
            return "mailgun"
        elif Config.RESEND_API_KEY:
            return "resend"
        elif Config.MAIL_USERNAME and Config.MAIL_PASSWORD:
            return "brevo"
        else:
            return "none"
    
    @staticmethod
    def is_email_configured():
        """Verifica si hay algún proveedor de email configurado"""
        return Config.get_email_provider() != "none"
    
    @staticmethod
    def get_best_from_email():
        """Obtiene el mejor email remitente basado en el proveedor activo"""
        provider = Config.get_email_provider()
        
        if provider == "mailgun":
            # Para Mailgun, usamos el dominio sandbox
            domain = Config.MAILGUN_DOMAIN
            if domain and "sandbox" in domain:
                return f"POS-ML <noreply@{domain}>"
            else:
                return Config.MAILGUN_FROM_EMAIL
        elif provider == "resend":
            return Config.RESEND_FROM_EMAIL
        elif provider == "brevo":
            return Config.MAIL_DEFAULT_SENDER
        else:
            return "POS-ML System <noreply@pos-ml.com>"