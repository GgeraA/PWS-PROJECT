# Gunicorn configuration for Render - OPTIMIZADO
import multiprocessing
import os

# ==================== CONFIGURACIÓN RENDER ====================
bind = "0.0.0.0:" + os.environ.get("PORT", "5000")

# Workers (optimizado para plan free)
workers = 2  # ✅ 2 workers para mejor concurrencia
worker_class = "sync"

# ==================== TIMEOUTS (¡CRÍTICO!) ====================
# Render Free Plan tiene timeout de 30s, ponemos menos
timeout = 29  # ✅ ¡IMPORTANTE! Menos de 30 segundos
keepalive = 5

# ==================== LIMITS ====================
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# ==================== OPTIMIZACIONES RENDER ====================
# Preload puede causar problemas con algunas librerías en Render
preload_app = False  # ✅ Desactivar para evitar problemas

# ==================== LOGGING ====================
accesslog = "-"
errorlog = "-"
loglevel = "info"

# ==================== DEBUG INFO ====================
print(f"🚀 Gunicorn configurado para Render:")
print(f"   • Workers: {workers}")
print(f"   • Timeout: {timeout}s (¡menos que límite Render de 30s!)")
print(f"   • Bind: {bind}")
print(f"   • Preload: {preload_app}")