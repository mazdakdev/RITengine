from django_filters import rest_framework as filters
from engine.models import Message

class BookmarkFilter(filters.FilterSet):
    text = filters.CharFilter(field_name="text", lookup_expr='icontains')

    class Meta:
        model = Message
        fields = ['text']
