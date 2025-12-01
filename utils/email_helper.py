import smtplib
import time
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from config import Config  # ✅ ¡AGREGAR ESTA LÍNEA!
import logging

logger = logging.getLogger(__name__)

def send_email(to_email, subject, body):
    """
    Envía correo usando SMTP - CORREGIDO
    """
    start = time.time()
    
    print(f"📧 SEND_EMAIL INICIADO para: {to_email}")
    
    try:
        # 1. VERIFICAR CONFIGURACIÓN
        print(f"🔧 Verificando configuración email...")
        
        # Verificar cada configuración requerida
        required_configs = {
            'MAIL_SERVER': Config.MAIL_SERVER,
            'MAIL_PORT': Config.MAIL_PORT,
            'MAIL_USERNAME': Config.MAIL_USERNAME,
            'MAIL_PASSWORD': Config.MAIL_PASSWORD,
            'MAIL_DEFAULT_SENDER': Config.MAIL_DEFAULT_SENDER
        }
        
        for key, value in required_configs.items():
            if not value:
                error_msg = f"❌ Configuración faltante: {key}"
                print(error_msg)
                return {"status": "error", "error": error_msg, "latency": 0}
            else:
                masked_value = "****" if "PASSWORD" in key else value
                print(f"   ✅ {key}: {masked_value}")
        
        # 2. CONFIGURAR TIMEOUT
        socket.setdefaulttimeout(15)
        
        # 3. CREAR MENSAJE
        message = MIMEMultipart()
        message["From"] = f"POS-ML System <{Config.MAIL_DEFAULT_SENDER}>"
        message["To"] = to_email
        message["Subject"] = Header(subject, 'utf-8')
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        print(f"🔧 Conectando a {Config.MAIL_SERVER}:{Config.MAIL_PORT}...")
        
        # 4. CONEXIÓN SMTP
        server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=15)
        
        try:
            print(f"🔧 Iniciando handshake SMTP...")
            server.ehlo()
            
            print(f"🔧 Activando TLS...")
            server.starttls()
            
            print(f"🔧 Handshake TLS...")
            server.ehlo()
            
            print(f"🔧 Autenticando como {Config.MAIL_USERNAME}...")
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            
            print(f"🔧 Enviando mensaje...")
            server.sendmail(
                Config.MAIL_DEFAULT_SENDER,
                to_email,
                message.as_string()
            )
            
            latency = round(time.time() - start, 3)
            success_msg = f"✅ Email ENVIADO a {to_email} en {latency}s"
            print(success_msg)
            
            return {"status": "success", "latency": latency}
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"❌ Error autenticación SMTP: {str(e)}"
            print(error_msg)
            return {"status": "error", "error": "Error de autenticación", "latency": round(time.time() - start, 3)}
            
        except smtplib.SMTPException as e:
            error_msg = f"❌ Error SMTP: {str(e)}"
            print(error_msg)
            return {"status": "error", "error": f"Error SMTP: {str(e)}", "latency": round(time.time() - start, 3)}
            
        finally:
            try:
                server.quit()
                print(f"🔧 Conexión cerrada")
            except:
                pass
                
    except socket.timeout:
        error_msg = "❌ Timeout conectando al servidor SMTP (15s)"
        print(error_msg)
        return {"status": "error", "error": error_msg, "latency": round(time.time() - start, 3)}
        
    except Exception as e:
        error_msg = f"❌ Error inesperado: {type(e).__name__}: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": f"Error: {str(e)}", "latency": round(time.time() - start, 3)}