import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE = { "dbname": "seguridad", "user": "postgres", "password": "ggerahl08ROM#", "host": "localhost", "port": 5432 }
    
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
    
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Config correo
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")
    
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecret")
    JWT_EXP_DELTA_SECONDS = 300  # 5 minutos