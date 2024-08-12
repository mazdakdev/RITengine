from django_filters import rest_framework as filters
from .models import Chat, Message

class ChatFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Chat
        fields = ['title']

class MessageFilter(filters.FilterSet):
    text = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Message
        fields = ['text']