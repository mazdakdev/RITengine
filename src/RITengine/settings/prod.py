from .base import *
import dj_database_url
from celery.schedules import crontab

DEBUG = False
SECRET_KEY = os.getenv("SECRET_KEY")

ALLOWED_HOSTS = [BACKEND_URL, FRONTEND_URL]

DATABASES = {"default": dj_database_url.config(default=os.getenv("DATABASE_URL"))}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f'{os.getenv("REDIS_URL")}/1',
    }
}
CELERY_BROKER_URL = f'{os.getenv("REDIS_URL")}/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = None
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,  # Redis task visibility timeout
    'retry_policy': {
        'max_retries': 3,
        'interval_start': 0,  # Retry immediately
        'interval_step': 0.2,  # Increase between retries
        'interval_max': 0.5,  # Max retry delay
    },
}

CELERY_BEAT_SCHEDULE = {
    'reset_plan_limits_daily': {
        'task': 'payment.tasks.reset_plan_limits',
        'schedule': crontab(hour=0, minute=0),  # Runs daily at midnight
    },
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PORT = os.getenv('EMAIL_PORT', default=587)
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

CSRF_TRUSTED_ORIGINS = [f"https://{BACKEND_URL}", f"https://{FRONTEND_URL}"]
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
