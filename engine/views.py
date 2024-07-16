from .models import Chat, Engine, Message
from rest_framework import generics
from django.http import StreamingHttpResponse
from django.conf import settings
from openai import AsyncOpenAI
from .serializers import StreamGeneratorSerializer, EngineSerializer, ChatSerializer, MessageSerializer
from rest_framework.permissions import IsAdminUser, IsAuthenticated

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class EngineListCreateView(generics.ListCreateAPIView):
    # permission_classes = [IsAdminUser,]
    queryset = Engine.objects.all()
    serializer_class = EngineSerializer

class EngineDetailView(generics.RetrieveUpdateDestroyAPIView):
    # permission_classes = [IsAdminUser, ]
    queryset = Engine.objects.all()
    serializer_class = EngineSerializer


#TODO: login and save chats


