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

    # Configuración de Email
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp-relay.brevo.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "9c4c04001@smtp-brevo.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "respaldogg20@gmail.com")
    MAIL_DEBUG = False
    MAIL_SUPPRESS_SEND = False

    # Configuración de entorno
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"