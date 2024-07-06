from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView, RegisterView
from drf_spectacular.utils import extend_schema , inline_serializer
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken
from dj_rest_auth.views import LoginView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from .serializers import UserSerializer
from .permissions import IsOTPVerified
from .api_docs import *
from django.urls import reverse

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
    request=GithubReqSerializer,
    responses={200: CustomLoginResponseSerializer},
    description="Github's Oauth"
)
class GitHubLogin(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = "https://127.0.0.1:3000/oath/callback/github"
    client_class = OAuth2Client

    def process_login(self):
        super().process_login()
        self.request.user.is_otp_verified = True
        self.request.user.save()



@extend_schema(
    request=CustomRegisterSerializer,
    responses={200: CustomRegisterResponseSerializer}
)
class CustomRegisterView(RegisterView):
    def post(self, request, *args, **kwargs):
        serializer = CustomRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(request)
            return Response({'message': 'Verification code sent successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=CustomRegisterSerializer,
    responses={200: CustomRegisterResponseSerializer}
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
                user.is_otp_verified = True
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


@extend_schema(
    responses={200: UserSerializer},
    parameters=[UserProfileParams]
)
class Profile(APIView):
    permission_classes = [IsAuthenticated, IsOTPVerified]

    def get(self, request, *args, **kwargs):
        user = request.user
        user_serializer = UserSerializer(user)
        return Response(user_serializer.data, status=status.HTTP_200_OK)


class ChangeUsername(APIView):
    permission_classes = [IsAuthenticated, IsOTPVerified]
    
    def post(self, request, *args, **kwargs):
        serializer = ChangeUsernameSerializer(data=request.data)
        if serializer.is_valid():
            new_username = serializer.validated_data['username']
            user = request.user
            user_serializer = UserSerializer(user)
            try:
                if user.username == new_username:
                    return Response({"message": "new username is the same with the old one."}, status=status.HTTP_400_BAD_REQUEST)

                if User.objects.filter(username=new_username).exists():
                    return Response({"message": "Username already taken."}, status=status.HTTP_400_BAD_REQUEST)
                 
               
                user.username = new_username
                user.save()
                return Response({"message": "Username changed successfully.", "user":user_serializer.data}, status=status.HTTP_200_OK)
            except ObjectDoesNotExist:
                return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
