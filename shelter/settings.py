from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ – в реальном проекте храните в переменных окружения
SECRET_KEY = 'django-insecure-&u5$wq+6n!w=*d@p7lbv%$e3t=8!x9z2q0r1s2t3u4v5w6x7y8z9'

DEBUG = True

ALLOWED_HOSTS = ['shelter-q6qb.onrender.com', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://shelter-q6qb.onrender.com']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_filters',
    'accounts',
    'animals',
    'reports',
    'django_otp.plugins.otp_static',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'shelter.urls'

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

WSGI_APPLICATION = 'shelter.wsgi.application'

# База данных PostgreSQL
# Можно переопределять параметры через переменные окружения (удобно для Docker/демо).
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('POSTGRES_DB', 'shelter_db_3jjd'),
        'USER': os.environ.get('POSTGRES_USER', 'shelter_db_3jjd_user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'riKTsX3uvPcqfYHYWXGMW0IHBx6EoscM'),
        'HOST': os.environ.get('POSTGRES_HOST', 'dpg-d8jd7k6k1jcs73f7f24g-a'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# Во время запуска автотестов по умолчанию используем SQLite (в памяти),
# чтобы тесты работали на любой машине без установленного PostgreSQL.
#
# Переключение на PostgreSQL для тестов:
#   DJANGO_TEST_USE_POSTGRES=1
# или более явный вариант:
#   DJANGO_TEST_DB=postgres
def _is_running_tests() -> bool:
    if 'test' in sys.argv:
        return True
    # При запуске через pytest sys.argv может не содержать "test".
    if 'pytest' in sys.modules:
        return True
    if os.environ.get('PYTEST_CURRENT_TEST'):
        return True
    return False


if _is_running_tests():
    test_db = (os.environ.get('DJANGO_TEST_DB') or '').strip().lower()
    use_postgres = os.environ.get('DJANGO_TEST_USE_POSTGRES') == '1' or test_db == 'postgres'
    if not use_postgres:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# AUTHENTICATION_BACKENDS = [
#     'django_otp.backends.OTPBackend',
#     'django.contrib.auth.backends.ModelBackend',
# ]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise: serve compressed, hashed static files in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
OTP_LOGIN_URL = 'accounts:2fa_verify'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Email – для напоминаний
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Бэкенд для отправки писем
EMAIL_HOST = 'smtp.gmail.com'         # Адрес SMTP-сервера (например, для Яндекса)
EMAIL_PORT = 465                      # Порт для SSL (или 587 для TLS)
EMAIL_USE_SSL = True                  # Использовать SSL (или EMAIL_USE_TLS = True)
EMAIL_HOST_USER = 'dashaband21@gmail.com'      # Ваш email для авторизации
EMAIL_HOST_PASSWORD = 'gdzw odfq ksdn vjt' # Пароль или токен доступа
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER   # Адрес, от которого будут приходить письма

HTTPS_MODE = os.environ.get('HTTPS_MODE', '').strip().lower()

# HTTPS_MODE=direct  -> standalone HTTPS server, no redirect loop
# HTTPS_MODE=proxy   -> reverse proxy terminates TLS and forwards to Django
if HTTPS_MODE in {'direct', 'proxy'}:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

if HTTPS_MODE == 'proxy':
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    SECURE_SSL_REDIRECT = False