# Gunicorn configuration for Kirokiro production
# Location: /home/kirokiro/kirokiro/gunicorn.conf.py (or project root)
# Usage: gunicorn -c gunicorn.conf.py kirokiro.wsgi:application

import multiprocessing
import os

# Server socket
bind = "unix:/run/gunicorn/kirokiro.sock"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/gunicorn/kirokiro-access.log"
errorlog = "/var/log/gunicorn/kirokiro-error.log"
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True

# Process naming
proc_name = "kirokiro-gunicorn"

# Server mechanics
daemon = False
pidfile = "/run/gunicorn/kirokiro.pid"
umask = 0o007
user = "www-data"
group = "www-data"

# SSL (handled by Nginx, do not enable here)
keyfile = None
certfile = None

# Application
wsgi_app = "kirokiro.wsgi:application"

# Preload app for better performance with workers
preload_app = True

# Environment
raw_env = [
    f"DJANGO_SETTINGS_MODULE=kirokiro.settings",
]

def on_starting(server):
    """Log when master process starts."""
    server.log.info("Starting Gunicorn for Kirokiro")

def on_reload(server):
    server.log.info("Reloading Gunicorn workers")

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_exit(server, worker):
    server.log.info("Worker exited (pid: %s)", worker.pid)
