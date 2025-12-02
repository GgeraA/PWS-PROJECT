import os
import requests
import json
import logging

logger = logging.getLogger(__name__)

class BrevoService:
    @staticmethod
    def send_email(to_email, subject, text_body, html_body=None):
        """
        Envía email usando Brevo API HTTP - 100% con variables de entorno
        """
        try:
            # 1. OBTENER DE VARIABLES DE ENTORNO
            api_key = os.getenv('BREVO_API_KEY')
            
            if not api_key:
                logger.error("❌ BREVO_API_KEY no está configurada en variables de entorno")
                return {"success": False, "error": "BREVO_API_KEY no configurada"}
            
            # Email del remitente desde variables de entorno
            sender_email = os.getenv('BREVO_SENDER_EMAIL', 'noreply@pos-ml.com')
            
            print(f"📧 BREVO: Iniciando envío a {to_email}")
            print(f"📧 Remitente: {sender_email}")
            print(f"🔑 API Key configurada: {'✅ Sí' if api_key else '❌ No'}")
            
            # 2. Crear HTML si no se proporciona
            if not html_body:
                html_body = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #4f46e5;">{subject}</h2>
                    <div style="background: #f3f4f6; padding: 20px; border-radius: 8px;">
                        {text_body.replace(chr(10), '<br>')}
                    </div>
                    <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
                        Email automático - No responder
                    </p>
                </div>
                """
            
            # 3. Payload para Brevo API
            payload = {
                "sender": {
                    "name": "POS-ML System",
                    "email": sender_email
                },
                "to": [{
                    "email": to_email,
                    "name": to_email.split('@')[0] if '@' in to_email else to_email
                }],
                "subject": subject,
                "htmlContent": html_body,
                "textContent": text_body
            }
            
            # 4. Headers con API Key de variables de entorno
            headers = {
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json"
            }
            
            print(f"📤 Enviando a API Brevo...")
            
            # 5. Enviar request
            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers=headers,
                data=json.dumps(payload),
                timeout=15
            )
            
            print(f"📥 Respuesta Brevo HTTP: {response.status_code}")
            
            # 6. Verificar respuesta
            if response.status_code == 201:
                response_data = response.json()
                print(f"✅ Brevo: Email enviado exitosamente")
                
                return {
                    "success": True,
                    "provider": "brevo",
                    "message_id": response_data.get('messageId'),
                    "status_code": response.status_code
                }
            else:
                error_msg = f"Brevo API error {response.status_code}"
                print(f"❌ {error_msg}")
                print(f"📄 Detalles: {response.text[:200]}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "details": response.text[:200],
                    "provider": "brevo",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            error_msg = "Brevo API timeout (15s)"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg, "provider": "brevo"}
            
        except Exception as e:
            error_msg = f"Brevo exception: {type(e).__name__}: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg, "provider": "brevo"}
    
    @staticmethod
    def test_connection():
        """Prueba la conexión con Brevo usando variables de entorno"""
        try:
            api_key = os.getenv('BREVO_API_KEY')
            
            if not api_key:
                print("❌ BREVO_API_KEY no configurada en variables de entorno")
                return False
            
            headers = {
                "accept": "application/json",
                "api-key": api_key
            }
            
            response = requests.get(
                "https://api.brevo.com/v3/account",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                account_info = response.json()
                print(f"✅ Conexión Brevo exitosa")
                print(f"📧 Email de cuenta: {account_info.get('email', 'N/A')}")
                return True
            else:
                print(f"❌ Error Brevo HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False