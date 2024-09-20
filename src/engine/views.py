from django.shortcuts import get_object_or_404
from rest_framework import generics
from django.conf import settings
from openai import AsyncOpenAI
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from share.views import GenerateShareableLinkView, BaseViewersListView, SharedRetrieveUpdateDestroyView
from rest_framework.response import Response
from .filters import ChatFilter, MessageFilter
from collections import defaultdict
from share.permissions import IsOwnerOrViewer
from .pagination import MessageCursorPagination
from django.db.models import Max
from django.db.models import Q
from .serializers import (
    EngineSerializer,
    ChatSerializer,
    MessageSerializer,
    AssistSerializer,
    EngineCategorySerializer
)

from .models import (
    Chat,
    Engine,
    Message,
    Assist,
    EngineCategory
)


client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class EngineListCreateView(generics.ListCreateAPIView):
    queryset = Engine.objects.all()
    serializer_class = EngineSerializer
    pagination_class = PageNumberPagination

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]

class EngineDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Engine.objects.all()
    serializer_class = EngineSerializer
    lookup_field = 'id'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

class UserChatsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = ChatSerializer
    pagination_class = PageNumberPagination
    filterset_class = ChatFilter

    def get_queryset(self):
        user = self.request.user
        chats = Chat.objects.filter(user=user).annotate(
            last_message_time=Max("messages__timestamp")
        ).order_by("-last_message_time")

        return chats

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        grouped_data = self.group_by_date(serializer.data)
        return Response(grouped_data)

    def group_by_date(self, data):
        grouped_chats = defaultdict(list)
        for item in data:
            date_key = item['created_at'].split("T")[0]
            grouped_chats[date_key].append(item)
        return grouped_chats

class UserChatsDetailView(SharedRetrieveUpdateDestroyView):
    serializer_class = ChatSerializer
    queryset = Chat.objects.all()
    lookup_field = 'slug'

class ChatsMessagesListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrViewer]
    serializer_class = MessageSerializer
    pagination_class = MessageCursorPagination
    filterset_class = MessageFilter
    lookup_field = 'slug'

    def get_queryset(self):
        chat_slug = self.kwargs['slug']
        user = self.request.user
        queryset = Chat.objects.filter(Q(slug=chat_slug) & (Q(user=user) | Q(viewers=user))).distinct()
        chat = get_object_or_404(queryset)
        return Message.objects.filter(chat=chat).order_by('timestamp')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context

class GenerateChatLinkView(GenerateShareableLinkView):
    def get_object(self):
        return get_object_or_404(Chat, slug=self.kwargs.get('slug'))

class AssistsListCreateView(generics.ListCreateAPIView):
    serializer_class = AssistSerializer
    lookup_field = 'id'
    queryset = Assist.objects.all()
    pagination_class = PageNumberPagination

class AssistsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Assist.objects.all()
    serializer_class = AssistSerializer
    lookup_field = 'id'
    pagination_class = PageNumberPagination


class EngineCategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = EngineCategorySerializer
    lookup_field = 'id'
    queryset = EngineCategory.objects.filter(is_default=False)
    pagination_class = PageNumberPagination

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]

class EngineCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = EngineCategory.objects.all()
    serializer_class = EngineCategorySerializer
    lookup_field = 'id'
    pagination_class = PageNumberPagination

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]


class ChatViewersListView(BaseViewersListView):
    def get_object(self):
        chat_slug = self.kwargs.get('slug')
        return get_object_or_404(Chat, slug=chat_slug)
