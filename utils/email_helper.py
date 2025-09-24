import smtplib
import ssl
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

def send_email(to_email, subject, body):
    """
    Envía un correo electrónico usando SMTP.
    Retorna dict con resultado y latencia.
    """
    start = time.time()
    try:
        # Construcción del mensaje
        message = MIMEMultipart()
        message["From"] = Config.MAIL_USERNAME
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Conexión segura con SMTP
        context = ssl.create_default_context()
        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
            server.starttls(context=context)
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.sendmail(Config.MAIL_USERNAME, to_email, message.as_string())

        latency = round(time.time() - start, 3)
        return {"status": "success", "latency": latency}

    except Exception as e:
        latency = round(time.time() - start, 3)
        return {"status": "error", "error": str(e), "latency": latency}
