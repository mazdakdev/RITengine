from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import LegalDocumentViewSet, FaqDocumentView

router = DefaultRouter()
router.register(r'documents', LegalDocumentViewSet, basename='legaldocument')
urlpatterns = router.urls

urlpatterns += [
    path('faq/', FaqDocumentView.as_view(), name='faq-document')
]