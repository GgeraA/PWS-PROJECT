import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header  # 👈 AGREGAR ESTO
from config import Config
import logging

logger = logging.getLogger(__name__)

def send_email(to_email, subject, body):
    """
    Envía correo usando Brevo SMTP - CON CODIFICACIÓN UTF-8
    """
    start = time.time()
    
    # Validar configuración
    if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD, Config.MAIL_SERVER]):
        error_msg = "Configuración de Brevo incompleta. Verifica las variables de entorno."
        logger.error(error_msg)
        return {"status": "error", "error": error_msg, "latency": 0}
    
    try:
        # Crear mensaje CON CODIFICACIÓN UTF-8
        message = MIMEMultipart()
        message["From"] = f"System POS-ML <{Config.MAIL_DEFAULT_SENDER}>"
        message["To"] = to_email
        message["Subject"] = Header(subject, 'utf-8')  # 👈 CODIFICAR SUBJECT
        
        # Cuerpo del mensaje CON CODIFICACIÓN UTF-8
        message.attach(MIMEText(body, "plain", "utf-8"))  # 👈 ESPECIFICAR UTF-8
        
        print(f"🔧 Conectando a Brevo: {Config.MAIL_SERVER}:{Config.MAIL_PORT}")
        print(f"🔧 Usuario: {Config.MAIL_USERNAME}")
        
        # Conexión con Brevo
        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
            server.ehlo()
            server.starttls()  # Habilitar TLS
            server.ehlo()
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            
            # 👇 ENVIAR CON CODIFICACIÓN UTF-8
            server.sendmail(
                Config.MAIL_DEFAULT_SENDER,
                to_email, 
                message.as_string().encode('utf-8')  # 👈 CODIFICAR A UTF-8
            )

        latency = round(time.time() - start, 3)
        success_msg = f"✅ Email enviado via Brevo a {to_email} en {latency}s"
        print(success_msg)
        logger.info(success_msg)
        return {"status": "success", "latency": latency}

    except smtplib.SMTPAuthenticationError as e:
        latency = round(time.time() - start, 3)
        error_msg = f"❌ Error de autenticación Brevo: {str(e)}"
        print(error_msg)
        logger.error(error_msg)
        return {"status": "error", "error": "Error de autenticación. Verifica SMTP key.", "latency": latency}
        
    except Exception as e:
        latency = round(time.time() - start, 3)
        error_msg = f"❌ Error enviando email via Brevo: {str(e)}"
        print(error_msg)
        logger.error(error_msg)
        return {"status": "error", "error": f"Error de conexión: {str(e)}", "latency": latency}