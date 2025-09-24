import time
from twilio.rest import Client
import os

def send_sms(to_phone, message):
    """
    Envío real de SMS con Twilio.
    """
    start = time.time()
    try:
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        from_phone = os.getenv("TWILIO_PHONE_NUMBER")

        client.messages.create(
            body=message,
            from_=from_phone,
            to=to_phone
        )

        latency = round(time.time() - start, 3)
        return {"status": "success", "latency": latency}
    except Exception as e:
        latency = round(time.time() - start, 3)
        return {"status": "error", "error": str(e), "latency": latency}