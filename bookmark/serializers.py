from rest_framework import serializers
from engine.models import Message
from .models import Bookmark

class BookmarkSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField()
    message_text = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = ['id', 'user', 'message_id', 'viewers', 'shareable_key', 'message_text', 'created_at']
        read_only_fields = fields

    def get_message_text(self, obj):
        return obj.message.text

    def create(self, validated_data):
        message_id = validated_data.pop('message_id')
        message = Message.objects.get(id=message_id)
        user = self.context['request'].user
        bookmark = Bookmark.objects.create(user=user, message=message)
        return bookmark