from rest_framework import serializers
from bookmark.models import Bookmark
from .models import (
    Engine,
    Chat,
    Message,
    Assist,
    EngineCategory
)
from share.serializers import BaseShareableSerializer

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

class ChatSerializer(BaseShareableSerializer):
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["id", "username", "title", "slug", "viewers", "excerpt", "shareable_key", "created_at", "updated_at"]
        read_only_fields = ["created_at", "id", "shareable_key", "viewers", "slug", "user"] #TODO: excerpt

    def get_excerpt(self, obj):
        if obj.messages.first():
            return obj.messages.first().text[:150].strip() + "..."
        return None


class MessageSerializer(serializers.ModelSerializer):
    is_bookmarked = serializers.SerializerMethodField()
    projects_in = serializers.SerializerMethodField()
    reply_to = serializers.PrimaryKeyRelatedField(queryset=Message.objects.all(), required=False, allow_null=True)
    username = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'username',
            'is_bookmarked', 'projects_in',
            'text', 'sender', 'timestamp',
            'chat', 'engines', 'reply_to'
        ]

    def get_is_bookmarked(self, obj):
        """
        Checks if the message is bookmarked by the current user using the BookmarkCollection model.

        Returns:
            bool: True if the message is in the user's BookmarkCollection, False otherwise.
        """
        user = self.context.get("user")

        try:
            bookmark_collection = Bookmark.objects.get(user=user)
        except Bookmark.DoesNotExist:
            return False

        return obj in bookmark_collection.messages.all()

    def get_projects_in(self, obj):
        """
        Retrieves all associated project IDs for the given message.

        Returns:
            list: A list of project IDs associated with the message that belongs to the current user.
        """
        user = self.context.get("user")
        project_ids = obj.projects.filter(user=user).values_list('id', flat=True)
        return list(project_ids)

    def get_username(self, obj):
        return obj.chat.user.username


class AssistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assist
        fields = '__all__'
