from django.contrib import admin
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.urls import path, include
from django.conf.urls.static import static
from django.urls import re_path
from rest_framework import permissions
from django.conf import settings
from RITengine.admin import admin_site

urlpatterns = [
   path("admin/statistics", admin_site.urls),
   path("admin/", admin.site.urls),
   path("api/auth/", include("user.urls")),
   path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
   path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
   path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
   path("api/engine/", include("engine.urls")),
   path("api/legal/", include("legal.urls")),
   path("api/projects/", include("project.urls")),
   path("api/bookmark/", include("bookmark.urls")),
   path("api/share/", include("share.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
