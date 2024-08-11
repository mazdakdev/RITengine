"""
WSGI config for RITengine project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Set the default Django settings module for the 'wsgi' program.
environment = os.getenv('DJANGO_ENV', 'dev')  # Default to 'dev' if not set
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"RITengine.settings.{environment}")

application = get_wsgi_application()