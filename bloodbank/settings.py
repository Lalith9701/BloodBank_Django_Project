from pathlib import Path
import os
import logging

# ============================================================
# Load .env file — no third-party packages needed
# ============================================================
_env_path = Path(__file__).resolve().parent.parent / '.env'
if _env_path.exists():
    for _line in _env_path.read_text(encoding='utf-8', errors='ignore').splitlines():
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _key, _val = _line.split('=', 1)
            os.environ.setdefault(_key.strip(), _val.strip())

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# SECURITY
# ============================================================
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-bloodbank-project-key')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ============================================================
# APPLICATIONS
# ============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'accounts',
    'donors',
    'inventory',
    'requests_app',
    'notifications',
    'ratings',
]

AUTH_USER_MODEL = 'accounts.User'

# ============================================================
# MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bloodbank.urls'

# ============================================================
# TEMPLATES
# ============================================================
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
                'notifications.context_processors.unread_notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'bloodbank.wsgi.application'

# ============================================================
# DATABASE
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ============================================================
# PASSWORD VALIDATION
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================
# LOCALISATION
# ============================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ============================================================
# STATIC FILES
# ============================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# AUTHENTICATION
# ============================================================
LOGIN_URL = '/'                  # path to login page (root)
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Token expires after 1 day (in seconds: 60 * 60 * 24)
PASSWORD_RESET_TIMEOUT = 86400

# ============================================================
# EMAIL — Gmail SMTP with App Password
# ============================================================
_email_user = os.environ.get('EMAIL_HOST_USER', '')
_email_pass = os.environ.get('EMAIL_HOST_PASSWORD', '')

# If credentials are missing/placeholder, fall back to console backend
# so the app doesn't crash during development
if _email_user and _email_user != 'your-gmail@gmail.com' and _email_pass and _email_pass != 'your-16-char-app-password':
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = _email_user
    EMAIL_HOST_PASSWORD = _email_pass
    DEFAULT_FROM_EMAIL = f'Blood Bank Management <{_email_user}>'
    SERVER_EMAIL = _email_user
else:
    # Prints email to console — useful during development
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_HOST_USER = ''
    DEFAULT_FROM_EMAIL = 'Blood Bank Management <noreply@bloodbank.local>'

# ============================================================
# SITE DOMAIN
# ============================================================
SITE_DOMAIN = os.environ.get('SITE_DOMAIN', 'localhost:8000')
SITE_PROTOCOL = os.environ.get('SITE_PROTOCOL', 'http')

# ============================================================
# LOGGING — track email sending and errors
# ============================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'bloodbank.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'django.core.mail': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
