import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'avtopark-pro-dev-key-change-in-production')

DEBUG = os.getenv('DEBUG', 'true').lower() in {'1', 'true', 'yes', 'on'}

# Render va lokal hostlar uchun to'g'ridan-to'g'ri ruxsatlar
ALLOWED_HOSTS = [
    'avtopark-pro-2.onrender.com',
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
]
# Muhit o'zgaruvchisidan ham qo'shimcha qo'shish imkoniyati
env_hosts = os.getenv('ALLOWED_HOSTS', '')
if env_hosts:
    for h in env_hosts.split(','):
        h_clean = h.strip()
        if h_clean and h_clean not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(h_clean)

# ============ CORS Sozlamalari ============
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True  # <--- MUHIM: credentials: "include" ishlashi uchun shart!

# Vercel va lokal domenlarni kiritamiz
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://avtopark-pro.vercel.app",
]

env_cors = os.getenv('CORS_ALLOWED_ORIGINS', '')
if env_cors:
    for origin in env_cors.split(','):
        o_clean = origin.strip()
        if o_clean and o_clean not in CORS_ALLOWED_ORIGINS:
            CORS_ALLOWED_ORIGINS.append(o_clean)
# ==========================================

INSTALLED_APPS = [
    'daphne',  # Enable ASGI/WebSocket support
    'corsheaders',  # CORS uchun
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'api',
    'channels',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Doimo eng birinchi bo'lishi kerak!
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.BranchContextMiddleware',
    'core.middleware.EnterprisePermissionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'core.middleware.RussianResponseMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

REDIS_URL = os.getenv('REDIS_URL', '').strip()
if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {
        'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}
    }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {'timeout': 20},
    }
}

LANGUAGE_CODE = 'uz'
LANGUAGES = [('uz', 'O‘zbekcha'), ('ru', 'Русский')]
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

SESSION_COOKIE_AGE = 60 * 60 * 12

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# ============ CSRF sozlamalari ============
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://avtopark-pro-2.onrender.com",
    "https://avtopark-pro.vercel.app",
    "https://*.onrender.com",
    "https://*.vercel.app",
]

env_csrf = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if env_csrf:
    for origin in env_csrf.split(','):
        o_clean = origin.strip()
        if o_clean and o_clean not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(o_clean)

CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False
CSRF_FAILURE_VIEW = 'api.views.csrf_failure'
# ==========================================

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', os.getenv('REDIS_URL', 'redis://localhost:6379/1'))
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', os.getenv('REDIS_URL', 'redis://localhost:6379/2'))
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'

if not DEBUG:
    if not os.getenv('DJANGO_SECRET_KEY') or 'unsafe-development' in SECRET_KEY:
        raise RuntimeError('DJANGO_SECRET_KEY must be set when DEBUG=False')
    if '*' in ALLOWED_HOSTS:
        raise RuntimeError('ALLOWED_HOSTS must not contain * in production')
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'true').lower() in {'1','true','yes'}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'
