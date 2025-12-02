# utils/email_final.py
import os
import logging
from config import Config

logger = logging.getLogger(__name__)

class EmailServiceFinal:
    @staticmethod
    def send_email(to_email, subject, text_body, html_body=None):
        """
        Envía email - PRIORIDAD: Brevo API → Brevo SMTP → SendGrid → Resend
        """
        providers = [
            EmailServiceFinal._try_brevo_api,     # 1. Brevo API (mejor)
            EmailServiceFinal._try_brevo_smtp,    # 2. Brevo SMTP 
            EmailServiceFinal._try_sendgrid,      # 3. SendGrid
            EmailServiceFinal._try_resend         # 4. Resend
        ]
        
        for provider in providers:
            try:
                result = provider(to_email, subject, text_body, html_body)
                if result.get("success", False):
                    logger.info(f"✅ Email enviado con {result.get('provider')}")
                    return result
                else:
                    logger.warning(f"⚠️ {result.get('provider')} falló: {result.get('error', 'Unknown')}")
            except Exception as e:
                logger.warning(f"⚠️ {provider.__name__} exception: {e}")
                continue
        
        # Todos fallaron
        return {
            "success": False,
            "error": "Todos los proveedores fallaron",
            "providers_tried": len(providers)
        }
    
    @staticmethod
    def _try_brevo_api(to_email, subject, text_body, html_body=None):
        """Brevo API HTTP - FUNCIONA EN RENDER"""
        try:
            import requests
            import json
            
            api_key = os.getenv('BREVO_API_KEY')
            if not api_key:
                return {"success": False, "error": "BREVO_API_KEY no configurada", "provider": "brevo_api"}
            
            # Si no hay HTML, crear uno básico
            if not html_body:
                html_body = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px;">
                    <h3>{subject}</h3>
                    <p>{text_body.replace(chr(10), '<br>')}</p>
                </div>
                """
            
            payload = {
                "sender": {
                    "name": "POS-ML System",
                    "email": os.getenv('BREVO_SENDER_EMAIL', 'respaldogg20@gmail.com')
                },
                "to": [{"email": to_email, "name": to_email.split('@')[0]}],
                "subject": subject,
                "htmlContent": html_body,
                "textContent": text_body
            }
            
            headers = {
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json"
            }
            
            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers=headers,
                data=json.dumps(payload),
                timeout=15
            )
            
            if response.status_code == 201:
                return {
                    "success": True,
                    "provider": "brevo_api",
                    "message_id": response.json().get('messageId')
                }
            else:
                return {
                    "success": False,
                    "error": f"Brevo API {response.status_code}: {response.text[:100]}",
                    "provider": "brevo_api"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e), "provider": "brevo_api"}
    
    @staticmethod
    def _try_brevo_smtp(to_email, subject, text_body, html_body=None):
        """Brevo SMTP - puede funcionar en Render"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            username = os.getenv('BREVO_SMTP_USERNAME')
            password = os.getenv('BREVO_SMTP_PASSWORD')
            
            if not username or not password:
                return {"success": False, "error": "Credenciales Brevo SMTP faltan", "provider": "brevo_smtp"}
            
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = os.getenv('BREVO_FROM_EMAIL', 'respaldogg20@gmail.com')
            msg['To'] = to_email
            
            # Texto plano
            msg.attach(MIMEText(text_body, 'plain'))
            
            # HTML
            if not html_body:
                html_body = text_body.replace('\n', '<br>')
            msg.attach(MIMEText(f"<html><body>{html_body}</body></html>", 'html'))
            
            # Enviar
            server = smtplib.SMTP("smtp-relay.brevo.com", 587)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()
            
            return {"success": True, "provider": "brevo_smtp"}
            
        except Exception as e:
            return {"success": False, "error": str(e), "provider": "brevo_smtp"}
    
    @staticmethod
    def _try_sendgrid(to_email, subject, text_body, html_body=None):
        """SendGrid como fallback"""
        try:
            api_key = os.getenv('SENDGRID_API_KEY')
            if not api_key:
                return {"success": False, "error": "SENDGRID_API_KEY no configurada", "provider": "sendgrid"}
            
            import requests
            
            if not html_body:
                html_body = text_body.replace('\n', '<br>')
            
            payload = {
                "personalizations": [{"to": [{"email": to_email}], "subject": subject}],
                "from": {"email": "noreply@pos-ml.app", "name": "POS-ML System"},
                "content": [
                    {"type": "text/plain", "value": text_body},
                    {"type": "text/html", "value": f"<html><body>{html_body}</body></html>"}
                ]
            }
            
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=15
            )
            
            if response.status_code == 202:
                return {"success": True, "provider": "sendgrid"}
            else:
                return {"success": False, "error": f"SendGrid {response.status_code}", "provider": "sendgrid"}
                
        except Exception as e:
            return {"success": False, "error": str(e), "provider": "sendgrid"}
    
    @staticmethod
    def _try_resend(to_email, subject, text_body, html_body=None):
        """Resend como último recurso"""
        try:
            api_key = os.getenv('RESEND_API_KEY')
            if not api_key:
                return {"success": False, "error": "RESEND_API_KEY no configurada", "provider": "resend"}
            
            import resend
            resend.api_key = api_key
            
            if not html_body:
                html_body = text_body.replace('\n', '<br>')
            
            # Verificar si podemos usar Resend
            verified_email = os.getenv('RESEND_VERIFIED_EMAIL', '')
            if verified_email and to_email != verified_email:
                # Necesitaríamos dominio verificado
                return {"success": False, "error": "Requiere dominio verificado", "provider": "resend"}
            
            from_email = "onboarding@resend.dev" if verified_email else "noreply@pos-ml.com"
            
            response = resend.Emails.send({
                "from": f"POS-ML <{from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": f"<html><body>{html_body}</body></html>",
                "text": text_body
            })
            
            if response and response.get('id'):
                return {"success": True, "provider": "resend", "id": response.get('id')}
            else:
                return {"success": False, "error": "Resend no respondió", "provider": "resend"}
                
        except Exception as e:
            return {"success": False, "error": str(e), "provider": "resend"}