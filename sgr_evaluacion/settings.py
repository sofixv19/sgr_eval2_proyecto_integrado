"""
Django settings for sgr_evaluacion project — Evaluación Sumativa 2.

Cambios respecto a la Evaluación 1:
- Se agregan django.contrib.admin / auth / sessions / messages / contenttypes
  (necesarios para Django Admin y CRUD con base de datos).
- La configuración sensible (SECRET_KEY, DEBUG, ALLOWED_HOSTS, credenciales
  de base de datos) ya NO está escrita en este archivo: se carga desde un
  archivo .env mediante python-decouple (requisito de "Variables de Entorno").

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/
"""

from pathlib import Path

from decouple import Csv, config
from django.contrib.messages import constants as mensajes

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Seguridad / variables de entorno
# ---------------------------------------------------------------------------
# Todas estas variables se definen en un archivo .env (no versionado, ver
# .gitignore) a partir de la plantilla .env.example incluida en el proyecto.

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'comun',
    'cuentas',
    'delegaciones',
    'organizacion',
    'gestion',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'cuentas.middleware.LoginObligatorioMiddleware',
    'comun.auditoria.AuditoriaMiddleware',   # v2.1: auditoría de operaciones (RF-036)
]

# WhiteNoise sirve los archivos estáticos cuando DEBUG=False (producción en
# EC2). Si la librería no está instalada, el sitio sigue funcionando igual.
try:
    import whitenoise  # noqa: F401
except ImportError:
    pass
else:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

ROOT_URLCONF = 'sgr_evaluacion.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cuentas.context_processors.rol_usuario',
            ],
        },
    },
]

WSGI_APPLICATION = 'sgr_evaluacion.wsgi.application'


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
# Requisito de la Evaluación 2: persistencia en base de datos relacional
# (MySQL en la instancia EC2, administrable desde phpMyAdmin).
#
# DB_ENGINE controla el motor y se define en el .env:
#   - "mysql"  -> producción / EC2 (MySQL + phpMyAdmin). Requiere las
#                 variables DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT.
#   - "sqlite" -> desarrollo local rápido, sin instalar MySQL (por defecto).
#
# PyMySQL se usa como driver puro-Python de MySQL (se registra como
# reemplazo de mysqlclient en sgr_evaluacion/__init__.py), porque es más
# simple de instalar en Windows/EC2 que compilar mysqlclient.

DB_ENGINE = config('DB_ENGINE', default='sqlite')

if DB_ENGINE == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# Autenticación y sesiones
# ---------------------------------------------------------------------------
# Los mensajes de error usan la clase 'danger' de Bootstrap.
MESSAGE_TAGS = {mensajes.ERROR: 'danger'}

LOGIN_URL = 'cuentas:login'
LOGIN_REDIRECT_URL = '/'

# Bloqueo temporal tras intentos fallidos de inicio de sesión.
SGR_LOGIN_MAX_INTENTOS = config('SGR_LOGIN_MAX_INTENTOS', default=5, cast=int)
SGR_LOGIN_MINUTOS_BLOQUEO = config('SGR_LOGIN_MINUTOS_BLOQUEO', default=15, cast=int)

# Versión del sistema (ver CHANGELOG.md). 1.x = requerimientos de la Guía SGR;
# 2.0 = Nuevos requerimientos de octubre 2026.
SGR_VERSION = '2.1.2'

# Reglas de negocio parametrizables (Guía SGR, sección 13.1)
SGR_TOPE_CUMPLIMIENTO = config('SGR_TOPE_CUMPLIMIENTO', default=150, cast=int)   # % máximo del colaborador
SGR_EVIDENCIA_MAX_MB = config('SGR_EVIDENCIA_MAX_MB', default=5, cast=int)

# Versión 2.0 — Nuevos requerimientos (octubre 2026)
SGR_TOPE_ITEM = config('SGR_TOPE_ITEM', default=120, cast=int)                    # % máximo por ítem (regla 7)
SGR_MAX_INGRESOS_DIARIOS = config('SGR_MAX_INGRESOS_DIARIOS', default=7, cast=int)  # regla 3
SGR_PUNTOS_FELICITACION = 10      # cada felicitación suma 10 puntos (máx. 3 por período)
SGR_MAX_FELICITACIONES = 3
SGR_PUNTOS_RECLAMO = 20           # cada reclamo resta 20 puntos

# Versión 2.1 — Alcance mínimo de la Guía SGR (agenda colectiva, alertas)
SGR_DIAS_AVISO_COMPROMISO = config('SGR_DIAS_AVISO_COMPROMISO', default=3, cast=int)   # "próximo a vencer"
SGR_DIAS_SIN_REGISTRO = config('SGR_DIAS_SIN_REGISTRO', default=5, cast=int)           # alerta de inactividad
SGR_UMBRAL_COLECTIVO = config('SGR_UMBRAL_COLECTIVO', default=80, cast=int)             # RN-006
SGR_UMBRAL_AMBAR = config('SGR_UMBRAL_AMBAR', default=60, cast=int)                     # RN-008: % de lo esperado

# Evidencias subidas por los funcionarios. No se publican en una URL
# abierta: se entregan con la vista gestion:evidencia, que revisa permisos.
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

SESSION_COOKIE_AGE = 30 * 60              # la sesión expira tras 30 minutos
SESSION_SAVE_EVERY_REQUEST = True         # ...contados desde la última acción
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True            # JavaScript no puede leer la cookie
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Cabeceras de seguridad
X_FRAME_OPTIONS = 'DENY'                  # evita clickjacking
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'

# Solo se activan cuando el sitio tenga HTTPS (variable USAR_HTTPS en .env).
USAR_HTTPS = config('USAR_HTTPS', default=False, cast=bool)
SESSION_COOKIE_SECURE = USAR_HTTPS
CSRF_COOKIE_SECURE = USAR_HTTPS
SECURE_SSL_REDIRECT = USAR_HTTPS

# Hash de contraseñas: PBKDF2-SHA256 (valor por defecto de Django).
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

# ---------------------------------------------------------------------------
# Registro de eventos de seguridad (logs/seguridad.log)
# ---------------------------------------------------------------------------
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '{asctime} [{levelname}] {name}: {message}', 'style': '{'},
    },
    'handlers': {
        'archivo_seguridad': {
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'seguridad.log',
            'formatter': 'simple',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'sgr.seguridad': {'handlers': ['archivo_seguridad'], 'level': 'INFO', 'propagate': False},
        'django.security': {'handlers': ['archivo_seguridad'], 'level': 'WARNING', 'propagate': False},
    },
}
