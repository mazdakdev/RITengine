from drf_spectacular.utils import inline_serializer
from rest_framework import serializers
from .serializers import UserSerializer

CustomLoginResponseSerializer = inline_serializer(
    name='CustomLoginResponse',
    fields={
        'access': serializers.CharField(default="access token (5 min)"),
        'refresh': serializers.CharField(default="refresh token (1 day)"),
        'user': serializers.ListField(child=UserSerializer())
    }
)


GithubReqSerializer = inline_serializer(name="GithubReqSerializer", fields={
    'code': serializers.CharField()
})

CustomRegisterResponseSerializer = inline_serializer(
    name='CustomRegisterResponse',
    fields={
        'message': serializers.CharField(default="Verification code sent successfully."),
    }
)
