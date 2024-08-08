from rest_framework.viewsets import ModelViewSet
from .models import LegalDocument
from .serializers import LegalDocumentSerializer
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status
from rest_framework.permissions import IsAdminUser, AllowAny


class LegalDocumentViewSet(ModelViewSet):
    queryset = LegalDocument.objects.all()
    serializer_class = LegalDocumentSerializer
    pagination_class = None
    lookup_field = 'doc_type'


    def handle_exception(self, exc):
        if isinstance(exc, NotFound):
            return Response({
                'status': 'error',
                'details': 'Legal Document Not Found',
                'error_code': 'document_not_found'
            }, status=status.HTTP_404_NOT_FOUND)

        return super().handle_exception(exc)

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        else:
            return [IsAdminUser()]