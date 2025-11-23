import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE = { 
        "database": "seguridad",  
        "user": "postgres", 
        "password": "123456", 
        "host": "localhost", 
        "port": 5432 
    }
    
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Config correo - CORREGIDO
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp-relay.brevo.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "9c4c04001@smtp-brevo.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "respaldogg20@gmail.com")
    
    # Configuraciones adicionales importantes para Flask-Mail
    MAIL_DEBUG = False
    MAIL_SUPPRESS_SEND = False
    
    JWT_EXP_DELTA_SECONDS = 300  # 5 minutos