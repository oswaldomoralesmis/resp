# ============================================================
# REEMPLAZAR la seccion DATABASES en settings.py con esto:
# ============================================================

import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'resp_db'),
        'USER': os.environ.get('DB_USER', 'resp_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'resp_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            # Fuerza UTF-8 y evita que psycopg2 lea vars de entorno de Windows
            'client_encoding': 'UTF8',
            'connect_timeout': 10,
            'options': '-c client_encoding=UTF8',
        },
    }
}
