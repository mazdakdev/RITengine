from django.urls import path
from .views import LegalDocumentViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'', LegalDocumentViewSet, basename='legaldocument')


urlpatterns = router.urls