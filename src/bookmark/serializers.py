from rest_framework import serializers
from engine.models import Message
from .models import Bookmark
from engine.serializers import MessageSerializer

class BookmarkSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(write_only=True)
    message = MessageSerializer(read_only=True)

    class Meta:
        model = Bookmark
        fields = [
                'id', 'user', 'message_id',
                'message','viewers', 'shareable_key',
                'created_at'
            ]
        read_only_fields = fields

    def create(self, validated_data):
        message_id = validated_data.pop('message_id')
        message = Message.objects.get(id=message_id)
        user = self.context.get('user')
        bookmark = Bookmark.objects.create(user=user, message=message)
        return bookmark
