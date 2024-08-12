from django_filters import rest_framework as filters
from .models import Bookmark

class BookmarkFilter(filters.FilterSet):
    text = filters.CharFilter(field_name="message__text", lookup_expr='icontains')

    class Meta:
        model = Bookmark
        fields = ['message__text']