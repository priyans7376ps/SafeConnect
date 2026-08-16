# Gunicorn production configuration for SafeConnect (Flask + Flask-SocketIO)

import os

bind = os.getenv("BIND", "0.0.0.0:5000")
workers = int(os.getenv("WORKERS", "1"))  # Eventlet / Gevent WebSocket single process mode
worker_class = "eventlet"
timeout = 120
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
