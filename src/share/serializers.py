from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class GenerateShareableLinkSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )

    def validate_user_ids(self, value):
        users = User.objects.filter(id__in=value)
        if len(users) != len(value):
            raise serializers.ValidationError("One or more user IDs are invalid.")
        return value
