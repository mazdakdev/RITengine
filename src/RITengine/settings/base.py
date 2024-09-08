from pathlib import Path
from datetime import timedelta
from RITengine.utils import parse_duration
import os


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "NOT-SECURE-SECRET-KEY"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Application definition

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "dj_rest_auth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth.registration",
    "allauth.socialaccount.providers.facebook",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    "corsheaders",
    "drf_spectacular",
    "phonenumber_field",
    "django_otp",
    "django_otp.plugins.otp_email",
    "django_otp.plugins.otp_totp",
    "channels",
    "django_filters",
]

INSTALLED_APPS += [
    "user",
    "engine",
    "legal",
    "project",
    "bookmark",
    "share",
    "stats"
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "RITengine.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        'DIRS': [
            BASE_DIR / 'user/templates',
            BASE_DIR / 'templates',
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": parse_duration(
        os.getenv("ACCESS_TOKEN_LIFETIME", default="5m")
    ),
    "REFRESH_TOKEN_LIFETIME": parse_duration(
        os.getenv("REFRESH_TOKEN_LIFETIME", default="1d")
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
}

WSGI_APPLICATION = "RITengine.wsgi.application"
ASGI_APPLICATION = "RITengine.asgi.application"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    'TOKEN_MODEL': None,
    "DEFAULT_THROTTLE_CLASSES": [
        "RITengine.throttles.CustomAnonRateThrottle",
        "RITengine.throttles.CustomUserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("ANONYMOUS_RATELIMIT"),
        "user": os.getenv("USERS_RATELIMIT"),
    },
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "RITengine.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "PAGE_SIZE_QUERY_PARAM": "page_size",
    "MAX_PAGE_SIZE": 100,
}



AUTH_USER_MODEL = "user.CustomUser"


SOCIALACCOUNT_PROVIDERS = {
    "github": {
        "APP": {
            "client_id": os.getenv("GITHUB_CLIENT_ID"),
            "secret": os.getenv("GITHUB_CLIENT_SECRET"),
            "key": ""
        }
    },

     'google': {
            'APP': {
                'client_id': os.getenv("GOOGLE_CLIENT_ID"),
                'secret': os.getenv("GOOGLE_CLIENT_SECRET"),
                'key': ''
            },
            'SCOPE': [
                'profile',
                'email',
            ],
            'AUTH_PARAMS': {
                'access_type': 'online',
            }
        }
}

REST_AUTH = {
    "USE_JWT": True,
    "TOKEN_MODEL": None,
}

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

REST_AUTH_REGISTER_SERIALIZER = "user.serializers.CustomRegisterSerializer"
REST_AUTH_LOGIN_SERIALIZER = "user.serializers.CustomLoginSerializer"
SOCIALACCOUNT_ADAPTER = "user.adapters.CustomSocialAccountAdapter"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_UNIQUE_EMAIL = True

FRONTEND_URL = os.getenv("FRONTEND_URL")
BACKEND_URL = os.getenv("BACKEND_URL")

SMS_PROVIDER = os.getenv("SMS_PROVIDER")
MELI_PAYAMAK_KEY = os.getenv("MELI_PAYAMAK_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
MAXIMUM_ALLOWED_USERNAME_CHANGE = 3
OAUTH_BASE_CALLBACK_URL = os.getenv("OAUTH_BASE_CALLBACK_URL")
TWO_FA_ANON_RATELIMIT = os.getenv("TWO_FA_ANON_RATELIMIT")
TWO_FA_USER_RATELIMIT = os.getenv("TWO_FA_USER_RATELIMIT")

DARKOB_SECRET = os.getenv("DARKOB_SECRET")
DARKOB_XFP = os.getenv("DARKOB_XFP")

# TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID")
# TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN")
# TWILIO_PHONE_NUMBER = env("TWILIO_PHONE_NUMBER")
