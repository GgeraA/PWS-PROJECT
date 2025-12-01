import smtplib
import time
import socket  # ✅ AGREGAR ESTO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from config import Config
import logging

logger = logging.getLogger(__name__)

def send_email(to_email, subject, body):
    """
    Envía correo usando Brevo SMTP - CON TIMEOUT
    """
    start = time.time()
    
    # Validar configuración
    if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD, Config.MAIL_SERVER]):
        error_msg = "Configuración de Brevo incompleta"
        logger.error(error_msg)
        return {"status": "error", "error": error_msg, "latency": 0}
    
    try:
        # ✅ CONFIGURAR TIMEOUT GLOBAL (10 segundos máximo)
        socket.setdefaulttimeout(10)
        
        # Crear mensaje
        message = MIMEMultipart()
        message["From"] = f"System POS-ML <{Config.MAIL_DEFAULT_SENDER}>"
        message["To"] = to_email
        message["Subject"] = Header(subject, 'utf-8')
        
        # Cuerpo del mensaje
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        # Conexión con timeout explícito
        logger.info(f"🔧 Conectando a Brevo (timeout: 10s)...")
        
        # ✅ CONEXIÓN CON TIMEOUT EXPLÍCITO
        server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=10)
        
        try:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            
            # Enviar email
            server.sendmail(
                Config.MAIL_DEFAULT_SENDER,
                to_email, 
                message.as_string()
            )
            
            latency = round(time.time() - start, 3)
            logger.info(f"✅ Email enviado a {to_email} en {latency}s")
            return {"status": "success", "latency": latency}
            
        finally:
            # ✅ CERRAR CONEXIÓN SIEMPRE
            try:
                server.quit()
            except:
                pass

    except socket.timeout:
        latency = round(time.time() - start, 3)
        error_msg = f"❌ Timeout conectando a Brevo (más de 10 segundos)"
        logger.error(error_msg)
        return {"status": "error", "error": "Timeout del servidor de email", "latency": latency}
        
    except smtplib.SMTPAuthenticationError as e:
        latency = round(time.time() - start, 3)
        error_msg = f"❌ Error de autenticación Brevo: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "error": "Error de autenticación", "latency": latency}
        
    except Exception as e:
        latency = round(time.time() - start, 3)
        error_msg = f"❌ Error enviando email: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "error": f"Error de conexión: {str(e)}", "latency": latency}