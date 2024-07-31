from django.shortcuts import get_object_or_404
from rest_framework import generics
from django.conf import settings
from openai import AsyncOpenAI
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from share.views import GenerateShareableLinkView
from .serializers import (
    EngineSerializer,
    ChatSerializer,
    MessageSerializer,
    AssistSerializer,
)

from .models import (
    Chat,
    Engine,
    Message,
    Assist,
)


client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class EngineListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser,]
    queryset = Engine.objects.all()
    serializer_class = EngineSerializer
    pagination_class = PageNumberPagination

class EngineDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser, ]
    queryset = Engine.objects.all()
    serializer_class = EngineSerializer
    lookup_field = 'id'

class UserChatsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = ChatSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(user=user)

class UserChatsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = ChatSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        user = self.request.user
        slug = self.kwargs['slug']
        return Chat.objects.filter(user=user, slug=slug)

class ChatsMessagesListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = MessageSerializer
    pagination_class = PageNumberPagination
    lookup_field = 'id'
    def get_queryset(self):
        chat_id = self.kwargs['id']
        chat = get_object_or_404(Chat, id=chat_id)

        if self.request.user != chat.user:
            return []

        return Message.objects.filter(chat=chat).order_by('timestamp')

class GenerateChatLinkView(GenerateShareableLinkView):
    def get_object(self):
        return get_object_or_404(Chat, id=self.kwargs.get('id'))

class AssistsListView(generics.ListCreateAPIView):
    serializer_class = AssistSerializer
    lookup_field = 'id'
    queryset = Assist.objects.all()
    pagination_class = PageNumberPagination

class AssistsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Assist.objects.all()
    serializer_class = AssistSerializer
    lookup_field = 'id'
    pagination_class = PageNumberPagination

