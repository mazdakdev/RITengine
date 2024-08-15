from rest_framework import serializers
from .models import LegalDocument, FaqDocument

class LegalDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalDocument
        fields = ['doc_type', 'content', "updated_at"]


class FaqDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaqDocument
        fields = ['question', 'answer', 'updated_at']