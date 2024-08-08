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
        fields = ["name", "prompt", "category"]


class EngineCategorySerializer(serializers.ModelSerializer):
    engines = EngineSerializer(many=True, read_only=True)
    class Meta:
        model = EngineCategory
        fields = "__all__"

class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = [
            "id", "title", "slug", "shareable_key", 
            "viewers", "created_at", "updated_at"]
        read_only_fields = ["created_at", "id", "shareable_key", "viewers"]

    def to_representation(self, queryset):
        grouped_chats = defaultdict(list)

        if isinstance(queryset, Chat):
            # if Chat instance is a single obj --> procced normally
            return super().to_representation(queryset) 
        
        for chat in queryset:
            date_key = chat.created_at.date().isoformat()
            grouped_chats[date_key].append({
                'id': chat.id,
                'title': chat.title,
                'slug': chat.slug,
                'created_at': chat.created_at,
                'updated_at': chat.updated_at,
            })

        return grouped_chats



class MessageSerializer(serializers.ModelSerializer):
    is_bookmarked = serializers.SerializerMethodField()
    class Meta:
        model = Message
        fields = '__all__'

    def get_is_bookmarked(self, obj):
        user = self.context['request'].user
        # if bookmark exists returns True
        return Bookmark.objects.filter(message=obj, user=user).exists()


class AssistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assist
        fields = '__all__'

