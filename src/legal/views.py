from rest_framework.viewsets import ModelViewSet
from .models import LegalDocument, FaqDocument
from .serializers import LegalDocumentSerializer, FaqDocumentSerializer
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework import generics


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


class FaqDocumentView(generics.ListCreateAPIView):
    queryset = FaqDocument.objects.all()
    serializer_class = FaqDocumentSerializer

    def post(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({
                'status': 'error',
                'details': 'You do not have permission to perform this action.'
            }, status=status.HTTP_403_FORBIDDEN)

        return super().post(request, *args, **kwargs)
