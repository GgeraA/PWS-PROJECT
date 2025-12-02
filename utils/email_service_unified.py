# utils/email_service_unified.py
import os
import logging
import requests
from config import Config

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_email(to_email, subject, text_body, html_body=None):
        """
        Envía email usando el mejor proveedor disponible
        """
        provider = Config.get_email_provider()
        
        if provider == "mailgun":
            return EmailService._send_mailgun(to_email, subject, text_body, html_body)
        elif provider == "resend":
            return EmailService._send_resend(to_email, subject, text_body, html_body)
        elif provider == "brevo":
            return EmailService._send_brevo(to_email, subject, text_body, html_body)
        else:
            return {
                "success": False,
                "error": "No hay proveedor de email configurado",
                "provider": "none"
            }
    
    @staticmethod
    def _send_mailgun(to_email, subject, text_body, html_body=None):
        """Envía email usando Mailgun API"""
        try:
            if not Config.MAILGUN_API_KEY or not Config.MAILGUN_DOMAIN:
                return {
                    "success": False,
                    "error": "Mailgun no configurado",
                    "provider": "mailgun"
                }
            
            url = f"https://api.mailgun.net/v3/{Config.MAILGUN_DOMAIN}/messages"
            
            data = {
                "from": Config.get_best_from_email(),
                "to": [to_email],
                "subject": subject,
                "text": text_body,
            }
            
            if html_body:
                data["html"] = html_body
            
            response = requests.post(
                url,
                auth=("api", Config.MAILGUN_API_KEY),
                data=data,
                timeout=15
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Email enviado con Mailgun a {to_email}")
                return {
                    "success": True,
                    "provider": "mailgun",
                    "id": response.json().get('id'),
                    "message": response.json().get('message', 'Email sent')
                }
            else:
                logger.error(f"Mailgun error {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"Mailgun error {response.status_code}",
                    "provider": "mailgun",
                    "details": response.text[:200]
                }
                
        except Exception as e:
            logger.error(f"Exception Mailgun: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "mailgun"
            }
    
    @staticmethod
    def _send_resend(to_email, subject, text_body, html_body=None):
        """Envía email usando Resend API"""
        try:
            if not Config.RESEND_API_KEY:
                return {
                    "success": False,
                    "error": "Resend no configurado",
                    "provider": "resend"
                }
            
            import resend
            resend.api_key = Config.RESEND_API_KEY
            
            params = {
                "from": Config.RESEND_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "text": text_body,
            }
            
            if html_body:
                params["html"] = html_body
            else:
                # HTML básico si no se proporciona
                params["html"] = f"""
                <div style="font-family: Arial, sans-serif;">
                    <h3>{subject}</h3>
                    <pre style="white-space: pre-wrap;">{text_body}</pre>
                </div>
                """
            
            response = resend.Emails.send(params)
            
            logger.info(f"✅ Email enviado con Resend a {to_email}")
            return {
                "success": True,
                "provider": "resend",
                "id": response.get('id')
            }
            
        except Exception as e:
            logger.error(f"Exception Resend: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "resend"
            }
    
    @staticmethod
    def _send_brevo(to_email, subject, text_body, html_body=None):
        """Envía email usando Brevo SMTP"""
        try:
            # Solo usar Brevo en desarrollo local
            if Config.FLASK_ENV == 'production' and os.getenv('RENDER'):
                return {
                    "success": False,
                    "error": "Brevo no disponible en producción (Render)",
                    "provider": "brevo"
                }
            
            from flask_mail import Message
            from app import mail  # Asegúrate de que 'app' sea tu instancia Flask
            
            msg = Message(
                subject=subject,
                sender=Config.MAIL_DEFAULT_SENDER,
                recipients=[to_email]
            )
            msg.body = text_body
            
            if html_body:
                msg.html = html_body
            
            mail.send(msg)
            
            logger.info(f"✅ Email enviado con Brevo a {to_email}")
            return {
                "success": True,
                "provider": "brevo"
            }
            
        except Exception as e:
            logger.error(f"Exception Brevo: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "brevo"
            }