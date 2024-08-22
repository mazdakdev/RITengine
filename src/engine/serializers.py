from rest_framework import serializers
from bookmark.models import Bookmark
from .models import (
    Engine,
    Chat,
    Message,
    Assist,
    EngineCategory
)
from collections import defaultdict

class StreamGeneratorSerializer(serializers.Serializer):
    engine_id = serializers.IntegerField()
    message = serializers.CharField(default="Send a greetings message for me and ask me to ask you a question to continue a conversation")

class EngineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Engine
        fields = ["id", "name", "prompt", "category"]


class EngineCategorySerializer(serializers.ModelSerializer):
    engines = EngineSerializer(many=True, read_only=True)
    class Meta:
        model = EngineCategory
        fields = "__all__"

class ChatSerializer(serializers.ModelSerializer):
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["id", "title", "slug", "viewers", "excerpt", "created_at", "updated_at"]
        read_only_fields = ["created_at", "id", "shareable_key", "viewers", "slug"] #TODO: excerpt

    def get_excerpt(self, obj):
        return obj.messages.first().text[:150].strip() + "..."

class MessageSerializer(serializers.ModelSerializer):
    is_bookmarked = serializers.SerializerMethodField()
    projects_in = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = '__all__'

    def get_is_bookmarked(self, obj):
        """
        Checks if the message is bookmarked by the current user.

        Returns:
            bool: True if a bookmark exists for this message and user, False otherwise.
        """
        user = self.context['request'].user
        return Bookmark.objects.filter(message=obj, user=user).exists()

    def get_projects_in(self, obj):
        """
        Retrieves all associated project IDs for the given message.

        Returns:
            list: A list of project IDs associated with the message that belongs to the current user.
        """
        user = self.context['request'].user
        project_ids = obj.projects.filter(user=user).values_list('id', flat=True)
        return list(project_ids)

class AssistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assist
        fields = '__all__'
