# utils/email_helper.py
import os
import logging
from config import Config

logger = logging.getLogger(__name__)

def send_email(to_email, subject, body):
    """
    Envía email usando Resend como primera opción, con fallback a Flask-Mail
    """
    # INTENTAR CON RESEND PRIMERO (funciona en Render)
    try:
        print(f"📧 Intentando enviar email con Resend a: {to_email}")
        
        from utils.email_resend import send_email_resend
        result = send_email_resend(to_email, subject, body)
        
        if result.get("status") == "success":
            print(f"✅ Resend exitoso! Latencia: {result.get('latency')}s")
            return result
        
        print(f"⚠️ Resend falló, intentando con Brevo...")
        
    except ImportError:
        print("📦 Resend no está instalado. Usando Brevo...")
    except Exception as e:
        print(f"⚠️ Error con Resend: {e}")

    # FALLBACK A BREVO/FLASK-MAIL (solo para desarrollo local)
    try:
        # Solo usar Brevo si estamos en desarrollo local
        if Config.FLASK_ENV == 'development' and not os.getenv('RENDER'):
            print(f"🔧 Modo desarrollo: usando Brevo para {to_email}")
            
            from flask_mail import Message
            from app import mail
            
            msg = Message(
                subject=subject,
                sender=Config.MAIL_DEFAULT_SENDER,
                recipients=[to_email]
            )
            msg.body = body
            msg.html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">POS-ML System</h2>
                <div style="background: #f3f4f6; padding: 20px; border-radius: 8px;">
                    <h3>{subject}</h3>
                    <pre style="white-space: pre-wrap; font-family: monospace;">{body}</pre>
                </div>
                <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
                    Este es un email automático. Por favor no responder.
                </p>
            </div>
            """
            
            mail.send(msg)
            return {"status": "success", "provider": "brevo", "note": "Desarrollo local"}
        else:
            return {"status": "error", "error": "No se pudo enviar email. Configura Resend para producción."}
            
    except Exception as e:
        error_msg = f"❌ Ambos métodos fallaron: {str(e)}"
        print(error_msg)
        return {"status": "error", "error": error_msg}