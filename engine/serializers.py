from rest_framework import serializers
from .models import (
    Engine,
    Chat,
    Message,
    Assist,
    EngineCategory
)


class StreamGeneratorSerializer(serializers.Serializer):
    engine_id = serializers.IntegerField()
    message = serializers.CharField(default="Send a greetings message for me and ask me to ask you a question to continue a conversation")

class EngineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Engine
        fields = ["name", "prompt", "category"]


class EngineCategorySerializer(serializers.ModelSerializer):
    engines = EngineSerializer(many=True, read_only=True)
    class Meta:
        model = EngineCategory
        fields = "__all__"

class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


class AssistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assist
        fields = '__all__'


#TODO: Readonly fields
#TODO: ALL APPS: explicit serializer fields