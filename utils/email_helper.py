import smtplib
import ssl
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG

def send_email(to_email, subject, body):
    """
    Envía un correo electrónico usando SMTP.
    Retorna dict con resultado y latencia.
    """
    start = time.time()
    try:
        # Construcción del mensaje
        message = MIMEMultipart()
        message["From"] = EMAIL_CONFIG["USER"]
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Conexión segura con SMTP
        context = ssl.create_default_context()
        with smtplib.SMTP(EMAIL_CONFIG["HOST"], EMAIL_CONFIG["PORT"]) as server:
            server.starttls(context=context)
            server.login(EMAIL_CONFIG["USER"], EMAIL_CONFIG["PASSWORD"])
            server.sendmail(EMAIL_CONFIG["USER"], to_email, message.as_string())

        latency = round(time.time() - start, 3)
        return {"status": "success", "latency": latency}

    except Exception as e:
        latency = round(time.time() - start, 3)
        return {"status": "error", "error": str(e), "latency": latency}
