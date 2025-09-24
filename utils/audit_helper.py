import time

def log_event(action, target, status, detail=""):
    """
    Registra eventos de auditoría (simulado).
    En un futuro puedes guardar en BD o archivo de logs.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] ACTION={action} TARGET={target} STATUS={status} DETAIL={detail}"
    print(log_line)
    return log_line