def send_email(to_email, subject, body):
    """
    Envía correo usando Brevo SMTP - CON MÁS DEBUG
    """
    import time
    import socket
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.header import Header
    
    start = time.time()
    
    print(f"📧 SEND_EMAIL INICIADO:")
    print(f"   Para: {to_email}")
    print(f"   Asunto: {subject[:50]}...")
    
    # 1. VERIFICAR CONFIGURACIÓN
    print(f"🔧 Verificando configuración...")
    required_config = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD']
    
    for config_key in required_config:
        config_value = getattr(Config, config_key, None)
        if not config_value:
            error_msg = f"❌ Configuración faltante: {config_key}"
            print(error_msg)
            return {"status": "error", "error": error_msg, "latency": 0}
        else:
            print(f"   ✅ {config_key}: {'****' if 'PASSWORD' in config_key else config_value}")
    
    try:
        # 2. CONFIGURAR TIMEOUT
        socket.setdefaulttimeout(15)  # 15 segundos máximo
        
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
            print(f"🔧 EHLO...")
            server.ehlo()
            
            print(f"🔧 STARTTLS...")
            server.starttls()
            
            print(f"🔧 EHLO again...")
            server.ehlo()
            
            print(f"🔧 Login como {Config.MAIL_USERNAME}...")
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            
            print(f"🔧 Enviando email...")
            server.sendmail(
                Config.MAIL_DEFAULT_SENDER,
                to_email, 
                message.as_string()
            )
            
            print(f"🔧 Cerrando conexión...")
            server.quit()
            
            latency = round(time.time() - start, 3)
            success_msg = f"✅ Email ENVIADO EXITOSAMENTE a {to_email} en {latency}s"
            print(success_msg)
            
            return {"status": "success", "latency": latency}
            
        except smtplib.SMTPException as e:
            error_msg = f"❌ Error SMTP: {str(e)}"
            print(error_msg)
            # Intentar ver error completo
            import sys
            print(f"❌ SMTP error details: {sys.exc_info()}")
            return {"status": "error", "error": f"Error SMTP: {str(e)}", "latency": round(time.time() - start, 3)}
            
        finally:
            try:
                server.quit()
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