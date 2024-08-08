from rest_framework import serializers
from engine.models import Message
from .models import Bookmark

class BookmarkSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField()
    message_text = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = ['id', 'user', 'message_id', 'message_text']

    def get_message_text(self, obj):
        return obj.message.text


    def __new__(cls, *args, **kwargs):
        cls.Meta.read_only_fields = [field for field in cls.Meta.fields]
        return super().__new__(cls, *args, **kwargs)

    def create(self, validated_data):
        message_id = validated_data.pop('message_id')
        message = Message.objects.get(id=message_id)
        user = self.context['request'].user
        bookmark = Bookmark.objects.create(user=user, message=message)
        return bookmark
