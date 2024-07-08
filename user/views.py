from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView, RegisterView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken
from dj_rest_auth.views import LoginView, UserDetailsView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from .permissions import IsOTPVerified
from .api_docs import *
import pyotp

User = get_user_model()


@extend_schema(
    request=GithubReqSerializer,
    responses={200: CustomLoginResponseSerializer},
    description="Github's Oauth"
)
class GitHubLoginView(SocialLoginView):
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
    responses={200: CustomLoginResponseSerializer}
)
class CustomLoginView(LoginView):
    serializer_class = CustomLoginSerializer


class CustomUserDetailsView(UserDetailsView):
    permission_classes = [IsAuthenticated, IsOTPVerified]
    serializer_class = UserSerializer


@extend_schema(
    request=OTPSerializer,
    responses={200: CustomLoginResponseSerializer}
)
class VerifyOTPView(APIView):
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
                    "refresh": str(refresh),
                    "access": str(access_token),
                    "user": user_serializer.data
                }, status=status.HTTP_200_OK)

            else:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    def post(request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.context['user']
            otp = user.generate_otp()
            return Response({'detail': 'OTP sent to email.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    def post(request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            user.save()
            return Response({'detail': 'Password has been reset.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TwoFaSetupView(APIView):
    permission_classes = [IsAuthenticated, IsOTPVerified]

    def get(self, request):
       user = request.user
       
       if not user.totp_key or user.two_fa_method != "google_auth":
            user.two_fa_method = "google_auth"
            user.totp_key = pyotp.random_base32()
            user.save()
        
       totp = pyotp.TOTP(user.totp_key)
       qr_code_url = totp.provisioning_uri(user.email, issuer_name="RITengine")
    
       return Response({'qr_code_url': qr_code_url})
