import os
import django

environment = os.getenv('DJANGO_ENV', 'dev')  # Default to 'dev' if not set
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"RITengine.settings.{environment}")

django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from engine.routing import websocket_urlpatterns
from engine.middleware import JWTAuthMiddlewareStack

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddlewareStack(
                URLRouter(
                    websocket_urlpatterns,
                )
            )
        ),
    }
)