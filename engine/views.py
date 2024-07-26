from django.shortcuts import get_object_or_404
from rest_framework import generics
from django.conf import settings
from openai import AsyncOpenAI
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from share.views import GenerateShareableLinkView, AccessSharedContentView
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

class EngineDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser, ]
    queryset = Engine.objects.all()
    serializer_class = EngineSerializer
    lookup_field = 'id'

class UserChatsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = ChatSerializer

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(user=user)

class UserChatsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = ChatSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        chat_id = self.kwargs['id']
        return Chat.objects.filter(user=user, id=chat_id)

class ChatsMessagesListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = MessageSerializer
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

class AssistsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Assist.objects.all()
    serializer_class = AssistSerializer
    lookup_field = 'id'


#TODO: Except HTTP 404
