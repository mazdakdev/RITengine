from .base import *
from dotenv import load_dotenv

load_dotenv(BASE_DIR.parent / ".env.dev")

DEBUG = True

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # CORS middleware should be at the top
] + MIDDLEWARE

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

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
