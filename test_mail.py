import os
from dotenv import load_dotenv
from app import create_app
from extensions import mail
from flask_mail import Message

load_dotenv()

def test_mail_configuration():
    app = create_app()
    
    with app.app_context():
        print("🔍 Verificando configuración de email:")
        print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
        print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
        print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
        print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
        print(f"MAIL_PASSWORD: {app.config.get('MAIL_PASSWORD')[:20]}...")
        print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
        
        # Intentar enviar un email de prueba
        try:
            msg = Message(
                subject="Test de configuración Flask-Mail",
                recipients=["respaldogg20@gmail.com"],
                body="Este es un email de prueba para verificar la configuración de Flask-Mail con Brevo."
            )
            mail.send(msg)
            print("✅ Email de prueba enviado exitosamente!")
            return True
        except Exception as e:
            print(f"❌ Error enviando email: {str(e)}")
            return False

if __name__ == "__main__":
    test_mail_configuration()