from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent
# Los tres se pueden sobreescribir desde .env (p.ej. en el servidor de
# pruebas/producción); si no está definido en .env, se mantiene el mismo
# comportamiento que tenía este archivo antes (uso en desarrollo local).
SECRET_KEY = config('SECRET_KEY', default='django-insecure-resp-tabasco-2025-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'crispy_forms',
    'crispy_bootstrap5',
    'servidores',
    'catalogos',
    'usuarios',
    'cargas',
    'reportes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'resp_project.urls'

# Configuración de sesiones
SESSION_COOKIE_AGE = 3600  # 1 hora en segundos (ajusta según necesites)
SESSION_SAVE_EVERY_REQUEST = True  # Actualiza la expiración en cada request
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # CLAVE: Expira al cerrar navegador

# Configuraciones adicionales de seguridad para sesiones
SESSION_COOKIE_SECURE = False  # Cambia a True si usas HTTPS en producción
SESSION_COOKIE_HTTPONLY = True  # Previene acceso desde JavaScript
SESSION_COOKIE_SAMESITE = 'Lax'  # Protección CSRF adicional
SESSION_COOKIE_NAME = 'sessionid_app3'

# La cookie de sesión ya tenía nombre propio (sessionid_app3) para no chocar
# con otras apps del mismo servidor, pero la de CSRF se había quedado con el
# nombre por defecto de Django ('csrftoken') — si otra app en el mismo
# dominio también usa ese nombre, el navegador manda el csrftoken de LA OTRA
# app y esta lo rechaza ("CSRF verification failed"). Con nombre propio se
# resuelve.
CSRF_COOKIE_NAME = 'csrftoken_app3'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'resp_project.wsgi.application'

import os as _os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='resp_db'),
        'USER': config('DB_USER', default='resp_user'),
        'PASSWORD': config('DB_PASSWORD', default='resp_password'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# Correo para el link de "recuperar contraseña". Por defecto se imprime en
# consola/log (no requiere SMTP, sirve para probar sin configurar nada) —
# para que el correo realmente llegue a una bandeja de entrada, defina en
# .env: EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend, más
# EMAIL_HOST/EMAIL_PORT/EMAIL_HOST_USER/EMAIL_HOST_PASSWORD/EMAIL_USE_TLS
# con los datos del servidor SMTP real.
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='RESP Tabasco <no-responder@tabasco.gob.mx>')

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

AUTH_USER_MODEL = 'usuarios.UsuarioRESP'
