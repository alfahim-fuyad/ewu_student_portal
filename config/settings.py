"""
Django settings for student_portal project.

Supports:
- Local development with PostgreSQL or SQLite
- Production deployment on Render with PostgreSQL
"""

import os
from pathlib import Path

from decouple import config, Csv
import dj_database_url


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-change-me-in-production-please-0987654321',
)

DEBUG = config(
    'DEBUG',
    default=False,
    cast=bool,
)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,.onrender.com',
    cast=Csv(),
)


# ============================================================
# CSRF
# ============================================================

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://*.onrender.com',
    cast=Csv(),
)


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
    'django.contrib.humanize',

    # Local apps
    'accounts',
    'students',
    'teachers',
    'academics',
    'attendance',
    'results',
    'fees',
    'notices',
    'chatbot',
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ============================================================
# URL / WSGI / ASGI
# ============================================================

ROOT_URLCONF = 'config.urls'

WSGI_APPLICATION = 'config.wsgi.application'

ASGI_APPLICATION = 'config.asgi.application'


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates'
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'accounts.views.user_profile_context',
            ],
        },
    },
]


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = (
    config('DATABASE_URL', default='') or ''
).strip()

SUPPORTED_DB_SCHEMES = (
    'postgres',
    'postgresql',
    'mysql',
    'pgsql',
    'postgis',
)


if DATABASE_URL and DATABASE_URL.startswith(SUPPORTED_DB_SCHEMES):

    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,

            # Keep database connections alive
            conn_max_age=600,

            # Local PostgreSQL usually doesn't use SSL.
            # Render/production will require SSL.
            ssl_require=not DEBUG,
        )
    }

else:

    # Fallback to SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ============================================================
# CUSTOM USER MODEL
# ============================================================

AUTH_USER_MODEL = 'accounts.User'


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },

    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',

        'OPTIONS': {
            'min_length': 6,
        },
    },

    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator'
    },

    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator'
    },
]


# ============================================================
# LOGIN / LOGOUT
# ============================================================

LOGIN_URL = 'accounts:login'

LOGIN_REDIRECT_URL = 'core:dashboard'

LOGOUT_REDIRECT_URL = 'accounts:login'


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Dhaka'

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


if not DEBUG:

    STATICFILES_STORAGE = (
        'whitenoise.storage.CompressedManifestStaticFilesStorage'
    )

else:

    STATICFILES_STORAGE = (
        'django.contrib.staticfiles.storage.StaticFilesStorage'
    )


# ============================================================
# MEDIA FILES
# ============================================================

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# PRODUCTION SECURITY
# ============================================================

if not DEBUG:

    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    SECURE_BROWSER_XSS_FILTER = True

    SECURE_CONTENT_TYPE_NOSNIFF = True

    X_FRAME_OPTIONS = 'DENY'


# ============================================================
# OPENAI / AI CHATBOT
# ============================================================

OPENAI_API_KEY = config(
    'OPENAI_API_KEY',
    default='',
)

OPENAI_API_URL = config(
    'OPENAI_API_URL',
    default='https://api.openai.com/v1/chat/completions',
)

OPENAI_MODEL = config(
    'OPENAI_MODEL',
    default='gpt-4o-mini',
)


# ============================================================
# CHATBOT SETTINGS
# ============================================================

CHATBOT_MAX_HISTORY = config(
    'CHATBOT_MAX_HISTORY',
    default=10,
    cast=int,
)

CHATBOT_ENABLED = bool(OPENAI_API_KEY)


# ============================================================
# EMAIL
# ============================================================

EMAIL_BACKEND = (
    'django.core.mail.backends.console.EmailBackend'
)

DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='noreply@studentportal.example',
)


# ============================================================
# LOGGING
# ============================================================

LOGGING = {
    'version': 1,

    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format':
            '[{asctime}] {levelname} {name}: {message}',

            'style': '{',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },

    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}