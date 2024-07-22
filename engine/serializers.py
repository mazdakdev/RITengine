from rest_framework import serializers
from .models import (
    Engine,
    Chat,
    Message,
    Assist,
    Bookmark
)


class StreamGeneratorSerializer(serializers.Serializer):
    engine_id = serializers.IntegerField()
    message = serializers.CharField(default="Send a greetings message for me and ask me to ask you a question to continue a conversation")

class EngineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Engine
        fields = '__all__'

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


class BookmarkSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Bookmark
        # fields = ['id', 'user', 'message_id']  # Include other fields as needed
        # read_only_fields = ['id', 'user']
        fields = "__all__"

    def create(self, validated_data):
        message_id = validated_data.pop('message_id')
        message = Message.objects.get(id=message_id)
        user = self.context['request'].user
        bookmark = Bookmark.objects.create(user=user, message=message)
        return bookmark


#TODO: Readonly fields