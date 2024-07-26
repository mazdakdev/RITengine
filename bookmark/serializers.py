from rest_framework import serializers
from engine.models import Message
from .models import Bookmark

class BookmarkSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Bookmark
        fields = ['id', 'user', 'message_id']  # Include other fields as needed
        read_only_fields = ['id', 'user']

    def create(self, validated_data):
        message_id = validated_data.pop('message_id')
        message = Message.objects.get(id=message_id)
        user = self.context['request'].user
        bookmark = Bookmark.objects.create(user=user, message=message)
        return bookmark
