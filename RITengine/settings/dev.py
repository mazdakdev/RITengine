from .base import *
from dotenv import load_dotenv

load_dotenv(".env.dev")

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# EMAIL_HOST = env('EMAIL_HOST')
# EMAIL_PORT = env('EMAIL_PORT', default=587)
# EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
# EMAIL_HOST_USER = env('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')