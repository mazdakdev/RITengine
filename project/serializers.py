from rest_framework import serializers
from engine.models import Message
from .models import Project

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "title", "description", "image"]
        read_only_fields = ['user']

class MessageIDSerializer(serializers.Serializer):
    message_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )

    def validate_message_ids(self, value):
        if not Message.objects.filter(id__in=value).exists():
            raise serializers.ValidationError("One or more messages do not exist.")
        return value