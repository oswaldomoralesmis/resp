# -*- coding: utf-8 -*-
"""Configuración de Gunicorn para el RESP en el servidor de pruebas.
Se usa como: gunicorn --config deploy/gunicorn.conf.py resp_project.wsgi:application
"""
import multiprocessing

# Solo loopback: nadie fuera de este servidor debe poder llegar directo a
# Gunicorn, siempre a través de nginx (que sí escucha en 0.0.0.0:9000).
bind = '127.0.0.1:9001'

workers = min(4, multiprocessing.cpu_count() * 2 + 1)
worker_class = 'sync'
# Las cargas de layout se procesan en un hilo aparte dentro del mismo
# worker (ver cargas/views.py, _lanzar_procesamiento) para no bloquear la
# respuesta HTTP; mientras ese hilo trabaja, el worker 'sync' igual debe
# poder mandarle su heartbeat al arbiter de Gunicorn, o lo mata por
# timeout (matando de paso el hilo a medio proceso). Este valor da margen
# de sobra para archivos grandes.
timeout = 300
graceful_timeout = 30
keepalive = 5

# stdout/stderr -> journald (ver: journalctl -u resp_project -f)
accesslog = '-'
errorlog = '-'
loglevel = 'info'
