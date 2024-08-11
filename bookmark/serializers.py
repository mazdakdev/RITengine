from rest_framework import serializers
from engine.models import Message
from .models import Bookmark
from collections import defaultdict

class BookmarkSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField()
    message_text = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = [
            'id', 'user', 'message_id', 'viewers',
            'shareable_key', 'message_text', "created_at"
            ]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Set all fields to read-only
            for field in self.fields.values():
                field.read_only = True



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

    def to_representation(self, queryset):
        grouped_bookmarks = defaultdict(list)

        if isinstance(queryset, Bookmark):
            # if Bookmark instance is a single obj --> procced normally
            return super().to_representation(queryset) 
        
        for bookmark in queryset:
            date_key = bookmark.created_at.date().isoformat()
            grouped_bookmarks[date_key].append({
                'id': bookmark.id,
                'user': bookmark.user.id,
                'message_id': bookmark.message_id,
                'message_text': bookmark.message.text,
            })

        return grouped_bookmarks
