from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class GenerateShareableLinkSerializer(serializers.Serializer):
    usernames = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )

    def validate_usernames(self, value):
        users = User.objects.filter(username__in=value)
        if len(users) != len(value):
            raise serializers.ValidationError("One or more usernames are invalid.")
        return value
