from rest_framework import serializers
from .models import Office, Form, Field

class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        exclude = ['id']
        extra_kwargs = {
            'slug': {'read_only': True}
        }

class FormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        exclude = ['id', 'office']
        extra_kwargs = {
            'slug': {'read_only': True}
        }

class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = '__all__'