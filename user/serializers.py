from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers, exceptions
from dj_rest_auth.registration.serializers import RegisterSerializer    
from dj_rest_auth.serializers import LoginSerializer
from allauth.account.adapter import get_adapter


class CustomRegisterSerializer(RegisterSerializer):
    username = None

    class Meta:
        model = get_user_model()
        fields = [
            "email"
            "password",
        ]

    def get_cleaned_data(self):
        return {
            "email": self.validated_data.get("email", ""),
            "password1": self.validated_data.get("password1", ""),
            "password2": self.validated_data.get("password2", ""),
        }

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        user.save()
        adapter.save_user(request, user, self)
        return user



class CustomLoginSerializer(LoginSerializer):
    username = None

    def authenticate(self, **options):
        return authenticate(self.context["request"], **options)

   