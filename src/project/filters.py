from django_filters import rest_framework as filters
from .models import Project

class ProjectFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='icontains') 

    class Meta:
        model = Project
        fields = ['title']