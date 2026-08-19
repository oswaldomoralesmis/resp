# -*- coding: utf-8 -*-
"""Configuración de Gunicorn para el RESP en el servidor de pruebas.
Se usa como: gunicorn --config deploy/gunicorn.conf.py resp_project.wsgi:application
"""
import multiprocessing

# Solo loopback: nadie fuera de este servidor debe poder llegar directo a
# Gunicorn, siempre a través de nginx (que sí escucha en 0.0.0.0:9000).
bind = '127.0.0.1:8001'

workers = min(4, multiprocessing.cpu_count() * 2 + 1)
worker_class = 'sync'
timeout = 60
graceful_timeout = 30
keepalive = 5

# stdout/stderr -> journald (ver: journalctl -u resp_project -f)
accesslog = '-'
errorlog = '-'
loglevel = 'info'
