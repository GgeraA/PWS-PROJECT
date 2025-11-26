# Gunicorn configuration for Render
import multiprocessing
import os

bind = "0.0.0.0:" + os.environ.get("PORT", "5000")
workers = 1  # Para plan free de Render
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True