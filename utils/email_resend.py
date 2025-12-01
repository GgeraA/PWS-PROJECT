# utils/email_resend.py
import os
import time
import logging
from config import Config

logger = logging.getLogger(__name__)

def send_email_resend(to_email, subject, body):
    """
    Enviar email usando Resend API - FUNCIONA EN RENDER
    """
    start = time.time()
    
    print(f"📧 RESEND: Iniciando envío a {to_email}")
    
    try:
        # 1. Obtener API key de entorno o config
        api_key = os.getenv('RESEND_API_KEY')
        if not api_key:
            print("❌ RESEND: API key no encontrada en variables de entorno")
            return {"status": "error", "error": "RESEND_API_KEY no configurada"}
        
        # 2. Importar resend DINÁMICAMENTE (evita error si no está instalado)
        try:
            import resend
        except ImportError:
            print("❌ RESEND: Paquete 'resend' no instalado. Ejecuta: pip install resend")
            return {"status": "error", "error": "Paquete resend no instalado"}
        
        # 3. Configurar API key
        resend.api_key = api_key
        
        # 4. Preparar parámetros
        # IMPORTANTE: Debes verificar este dominio en Resend primero
        # Para testing, puedes usar el dominio de prueba de Resend
        from_email = "onboarding@resend.dev"  # Email de prueba de Resend
        # O cuando verifiques tu dominio:
        # from_email = "noreply@tudominio.com"
        
        params = {
            "from": f"POS-ML System <{from_email}>",
            "to": [to_email],
            "subject": subject,
            "text": body,  # Versión texto plano
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">POS-ML System</h2>
                <div style="background: #f3f4f6; padding: 20px; border-radius: 8px;">
                    <h3>{subject}</h3>
                    <pre style="white-space: pre-wrap; font-family: monospace;">{body}</pre>
                </div>
                <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
                    Este es un email automático. Por favor no responder.
                </p>
            </div>
            """
        }
        
        print(f"📧 RESEND: Enviando email desde {from_email}...")
        
        # 5. Enviar email
        response = resend.Emails.send(params)
        
        latency = round(time.time() - start, 3)
        print(f"✅ RESEND: Email enviado exitosamente en {latency}s")
        print(f"📧 RESEND ID: {response.get('id', 'N/A')}")
        
        return {
            "status": "success", 
            "latency": latency, 
            "id": response.get('id'),
            "provider": "resend"
        }
        
    except Exception as e:
        latency = round(time.time() - start, 3)
        error_msg = f"❌ RESEND Error: {type(e).__name__}: {str(e)}"
        print(error_msg)
        
        # Log detallado para debugging
        import traceback
        traceback.print_exc()
        
        return {
            "status": "error", 
            "error": str(e), 
            "latency": latency,
            "provider": "resend"
        }