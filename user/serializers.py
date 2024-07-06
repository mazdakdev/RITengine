from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers, exceptions
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from allauth.account.adapter import get_adapter
from .utils import generate_otp, send_otp_email
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

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
        otp = generate_otp()
        send_otp_email(user.email , otp)
        user.otp = otp
        print(otp)
        user.otp_expiry_time = timezone.now() + timedelta(minutes=30)
        user.save()
        adapter.save_user(request, user, self)

        return user


class CustomLoginSerializer(LoginSerializer):
    username = None

    def authenticate(self, **options):
        return authenticate(self.context["request"], **options)


class CustomLoginResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['pk', 'email'] 

   
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['pk', 'email'] 

class OTPSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    email = serializers.EmailField()