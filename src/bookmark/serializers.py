from rest_framework import serializers
from engine.models import Message
from .models import Bookmark
from engine.serializers import MessageSerializer
from collections import defaultdict
from datetime import datetime

class BookmarkSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Bookmark
        fields = [
            'id', 'user', 'messages',
            'viewers', 'shareable_key',
            'created_at'
        ]
        read_only_fields = fields

    # def create(self, validated_data):
    #     message_id = validated_data.pop('message_id')
    #     message = Message.objects.get(id=message_id)
    #     user = self.context.get('user')
    #     bookmark = Bookmark.objects.create(user=user, message=message)
    #     return bookmark
    #
    def get_messages(self, obj):
        grouped_messages = defaultdict(list)

        for message in obj.messages.all():
            message_date = message.timestamp.strftime('%Y-%m-%d')
            grouped_messages[message_date].append(MessageSerializer(message).data)

        return grouped_messages

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['messages'] = self.get_messages(instance)
        return representation
