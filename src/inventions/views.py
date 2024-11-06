from django.shortcuts import render

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

from .models import (
    Office,
    Field,
    Form,
    Invention
)
from .serializers import OfficeSerializer, FormSerializer, FieldSerializer

class OfficeListView(generics.ListAPIView):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    pagination_class = PageNumberPagination
    # permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset
    
class FormListView(generics.ListAPIView):
    queryset = Form.objects.all()
    serializer_class = FormSerializer
    pagination_class = PageNumberPagination
    # permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

class FormDetailView(generics.RetrieveAPIView):
    queryset = Form.objects.all()
    serializer_class = FormSerializer
    lookup_field = 'slug'

    def get_object(self):
        queryset = self.get_queryset()
        slug = self.kwargs.get('slug')
        return get_object_or_404(queryset, office=slug)
    
class FieldListView(generics.ListAPIView):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer
    pagination_class = PageNumberPagination
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset