from .base import *
from dotenv import load_dotenv

SECRET_KEY = "NOT-SECURE-SECRET-KEY"

load_dotenv(BASE_DIR.parent / ".env.dev")

ALLOWED_HOSTS = ["*"]

DEBUG = True

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # CORS middleware should be at the top
] + MIDDLEWARE

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# EMAIL_HOST = os.getenv('EMAIL_HOST')
# EMAIL_PORT = os.getenv('EMAIL_PORT', default=587)
# EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', default=True)
# EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_FROM = os.getenv("EMAIL_FROM")
# OTP_EMAIL_SENDER = EMAIL_FROM

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

CELERY_BROKER_URL = 'redis://localhost:6380/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
