import smtplib
import ssl
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

def send_email(to_email, subject, body):
    """
    Envía un correo electrónico usando SMTP seguro (TLS/SSL).
    Retorna dict con resultado y latencia.
    """
    start = time.time()
    try:
        message = MIMEMultipart()
        message["From"] = Config.MAIL_USERNAME
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Crear contexto seguro con TLS 1.2 o superior
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED

        with smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT, context=context) as server:
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.sendmail(Config.MAIL_USERNAME, to_email, message.as_string())

        latency = round(time.time() - start, 3)
        return {"status": "success", "latency": latency}

    except Exception as e:
        latency = round(time.time() - start, 3)
        return {"status": "error", "error": str(e), "latency": latency}
