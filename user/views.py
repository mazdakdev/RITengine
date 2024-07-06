from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView, RegisterView
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken
from dj_rest_auth.views import LoginView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from .serializers import UserSerializer


User = get_user_model()

CustomLoginResponseSerializer = inline_serializer(
    name='CustomLoginResponse',
    fields={
        'access': serializers.CharField(default="access token (5 min)"),
        'refresh': serializers.CharField(default="refresh token (1 day)"),
        'user': serializers.ListField(child=UserSerializer())
    }
)


@extend_schema(
    request=inline_serializer(name="GithubReqSerializer", fields={
        'code': serializers.CharField()
    }),
    responses={200: CustomLoginResponseSerializer},
    description="Github's oauth",
)
class GitHubLogin(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = "https://127.0.0.1:3000/oath/callback/github"
    client_class = OAuth2Client


@extend_schema(
    request=CustomRegisterSerializer,
    responses={200: inline_serializer(
            name='CustomRegisterResponse',
            fields={
                'message': serializers.CharField(default="Verification code sent successfully."),
            }
        )}
)
class CustomRegisterView(RegisterView):
    def post(self, request, *args, **kwargs):
        serializer = CustomRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(request)
            return Response({'message': 'Verification code sent successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=CustomLoginSerializer,
    responses={200: CustomLoginResponseSerializer}
)
class CustomLoginView(LoginView):
    serializer_class = CustomLoginSerializer


@extend_schema(
    request=OTPSerializer,
    responses={200: CustomLoginResponseSerializer}
)
class VerifyOTP(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        otp = request.data.get('otp')
                
        if email and otp:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
            stored_otp = user.otp
            otp_expiry_time = user.otp_expiry_time
            current_time = timezone.now()

            if otp_expiry_time < current_time:
                return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)
            
            if str(otp) == str(stored_otp):
                user.otp = None
                user.save()
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token
                user_serializer = UserSerializer(user)

                return Response({
                    "refresh":str(refresh),
                    "access":str(access_token),
                    "user":user_serializer.data
                }, status=status.HTTP_200_OK)

            else:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"error": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)