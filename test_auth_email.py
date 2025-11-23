import os
from dotenv import load_dotenv
from app import create_app
from services.auth_service import send_email  # Ajusta esta importación según tu estructura

load_dotenv()

def test_auth_emails():
    app = create_app()
    
    with app.app_context():
        print("🔍 Probando envío de emails desde AuthService...")
        
        # Probar recuperación de usuario
        try:
            result = send_email(
                "hegelop329@gmail.com",  # Cambia por un email de prueba
                "Test Recuperación Usuario - POS-ML",
                "Este es un test del sistema de recuperación de usuario."
            )
            print(f"✅ Email de recuperación de usuario: {result}")
        except Exception as e:
            print(f"❌ Error en recuperación de usuario: {str(e)}")
        
        # Probar recuperación de contraseña
        try:
            result = send_email(
                "respaldogg20@gmail.com",  # Cambia por un email de prueba
                "Test Recuperación Contraseña - POS-ML", 
                "Este es un test del sistema de recuperación de contraseña."
            )
            print(f"✅ Email de recuperación de contraseña: {result}")
        except Exception as e:
            print(f"❌ Error en recuperación de contraseña: {str(e)}")

if __name__ == "__main__":
    test_auth_emails()