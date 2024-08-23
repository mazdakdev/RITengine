from rest_framework import serializers
from engine.models import Message
from .models import Project

class ProjectSerializer(serializers.ModelSerializer):
    messages_in = serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = ["id", "user", "title", "description", "image", "messages_in", "viewers", "shareable_key", "created_at", "updated_at"]
        read_only_fields = ['user',"created_at", "updated_at", "id"]

    def get_messages_in(self, obj):
        """
        Retrieves all associated message IDs for the given project.

        Returns:
            list: A list of message IDs associated with the project that belong to the current user.
        """
        user = self.context['request'].user
        message_ids = obj.messages.filter(chat__user=user).values_list('id', flat=True)
        return list(message_ids)

class MessageIDSerializer(serializers.Serializer):
    message_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )

    def validate_message_ids(self, value):
        if not Message.objects.filter(id__in=value).exists():
            raise serializers.ValidationError("One or more messages do not exist.")
        return value

class MessageProjectAssociationSerializer(serializers.Serializer):
    message_id = serializers.IntegerField()
    project_ids = serializers.ListField(
        child=serializers.IntegerField()
    )

    def validate_message_id(self, value):
        if not Message.objects.filter(id=value).exists():
            raise serializers.ValidationError("Message with the given ID does not exist.")
        return value

    def validate_project_ids(self, value):
        if not Project.objects.filter(id__in=value).exists():
            raise serializers.ValidationError("One or more Project IDs are invalid.")
        return value
