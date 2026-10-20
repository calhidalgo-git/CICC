import importlib.util
import os
import secrets
import shutil
import tempfile
import warnings
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
ON_VERCEL = bool(os.environ.get('VERCEL'))


def env_flag(name, default):
    return os.environ.get(name, default) == '1'


# En local el desarrollo arranca con DEBUG activo. En Vercel hay que activarlo de forma explícita.
DEBUG = env_flag('DEBUG', '0' if ON_VERCEL else '1')

_DEV_SECRET = 'local-prototype-only-change-before-deployment'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or _DEV_SECRET  # una variable vacía cuenta como no definida
# True cuando no se configuró una clave real y se usa una temporal (solo permitido en Vercel).
SECRET_KEY_EPHEMERAL = False
if not DEBUG and SECRET_KEY == _DEV_SECRET:
    if not ON_VERCEL:
        raise ImproperlyConfigured('Define DJANGO_SECRET_KEY con un valor aleatorio cuando DEBUG=0.')
    # En Vercel se permite arrancar sin clave para que la demo se pueda construir: la clave es aleatoria por proceso.
    # Las sesiones y los enlaces de recuperación dejan de valer al reiniciarse la instancia, y con varias instancias el
    # acceso puede fallar de forma intermitente. Define DJANGO_SECRET_KEY en Vercel para un despliegue estable.
    SECRET_KEY = secrets.token_urlsafe(64)
    SECRET_KEY_EPHEMERAL = True
    warnings.warn(
        'DJANGO_SECRET_KEY no está definida: se usa una clave temporal (solo para demostración).', stacklevel=1
    )

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver', '.vercel.app']
ALLOWED_HOSTS += [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = ['https://*.vercel.app']
CSRF_TRUSTED_ORIGINS += [o.strip() for o in os.environ.get('DJANGO_CSRF_ORIGINS', '').split(',') if o.strip()]

# Muestra las cuentas de demostración en la pantalla de acceso. Desactivado por defecto fuera de DEBUG.
SHOW_DEMO_CREDENTIALS = env_flag('SHOW_DEMO_CREDENTIALS', '1' if DEBUG else '0')

# Correo (recuperación de contraseña y avisos de resultado). Sin EMAIL_HOST los mensajes se imprimen en la consola del servidor.
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_BACKEND = (
    'django.core.mail.backends.smtp.EmailBackend' if EMAIL_HOST else 'django.core.mail.backends.console.EmailBackend'
)
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_flag('EMAIL_USE_TLS', '1')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'CICC <no-reply@localhost>')
# Dirección pública del sitio; se usa en los enlaces de los correos que se envían fuera de una petición.
SITE_URL = os.environ.get('SITE_URL', 'http://127.0.0.1:8000').rstrip('/')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'hub',
]
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware']
# WhiteNoise sirve los estáticos sin servidor adicional (necesario con DEBUG=0 en Vercel). Con DEBUG los sirve runserver.
if not DEBUG and importlib.util.find_spec('whitenoise'):
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')
MIDDLEWARE += [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
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
            ]
        },
    }
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('PGDATABASE', 'qahub'),
        'USER': os.environ.get('PGUSER', 'qahub'),
        'PASSWORD': os.environ.get('PGPASSWORD', ''),
        'HOST': os.environ.get('PGHOST', 'localhost'),
        'PORT': os.environ.get('PGPORT', '5432'),
    }
}
if os.environ.get('QA_SQLITE') == '1':
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'demo.sqlite3'}}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedStaticFilesStorage'
            if importlib.util.find_spec('whitenoise')
            else 'django.contrib.staticfiles.storage.StaticFilesStorage'
        )
    },
}
WHITENOISE_USE_FINDERS = True  # sirve static/ directamente, sin exigir collectstatic
MEDIA_ROOT = BASE_DIR / 'private_storage'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Lima'
USE_TZ = True

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'

if not DEBUG:
    # Producción: cookies solo por HTTPS, redirección y HSTS. Desactivable con DJANGO_SSL_REDIRECT=0 si un proxy ya lo hace.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_flag('DJANGO_SSL_REDIRECT', '1')
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7

# Vercel: el sistema de archivos es de solo lectura salvo /tmp, así que la base demo se copia allí en cada arranque en frío.
# Los cambios hechos en la demo publicada NO persisten entre despliegues ni entre instancias.
if ON_VERCEL:
    _TMP = Path(tempfile.gettempdir())  # /tmp en Vercel; es la única carpeta escribible
    _DB = _TMP / 'demo.sqlite3'
    if not _DB.exists():
        shutil.copy(BASE_DIR / 'demo.sqlite3', _DB)
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': _DB}}
    SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
    MEDIA_ROOT = _TMP / 'private_storage'
