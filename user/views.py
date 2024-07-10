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
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

class CompleteRegistrationView(APIView):
    def post(self, request):
        serializer = OTPSerializer(data=request.data)
        if serializer.is_valid():
            otp_code = serializer.validated_data['otp']
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)

                if not user.is_email_verified:
                    if user.otp_secret:
                        totp = pyotp.TOTP(user.otp_secret, interval=300)

                        if totp.verify(otp_code):
                            user.is_email_verified = True
                            user.save()
                            refresh = RefreshToken.for_user(user)
                            access_token = refresh.access_token
                            user_serializer = UserSerializer(user)

                            return Response({
                                'message': 'Email verified.',
                                'access': str(access_token),
                                'refresh': str(refresh),
                                'user': user_serializer.data
                            }, status=status.HTTP_200_OK)
                        else:
                            return Response({'message': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({'message': 'User OTP Secret not found.'}, status=status.HTTP_400_BAD_REQUEST)
                return Response({'message': "User's email has already been verified."})
            except User.DoesNotExist:
                return Response({'message': 'Invalid email.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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


class TwoFASetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TwoFASetupSerializer(data=request.data)
        if serializer.is_valid():
            method = serializer.validated_data.get('method')
            user = request.user

            if not user.is_2fa_enabled:

                if method == 'google_auth' :
                    secret = pyotp.random_base32()
                    user.otp_secret = secret
                    user.save()
                    return Response({'google_auth_secret': secret}, status=status.HTTP_200_OK)

                elif method == 'sms':
                    pass
                    # phone_number = serializer.validated_data.get('phone_number')
                    # # Store the phone number in the user profile (you need to add this field)
                    # user.phone_number = phone_number
                    # user.save()
                    # # Send verification SMS using Twilio
                    # client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')
                    # otp_code = pyotp.TOTP(user.otp_secret).now()
                    # client.messages.create(body=f'Your OTP code is {otp_code}', from_='+1234567890', to=phone_number)
                    # return Response({'message': 'SMS sent'}, status=status.HTTP_200_OK)

                elif method == 'email':
                    otp_code = pyotp.TOTP(user.otp_secret).now()
                    user.send_mail('Your 2FA Code',
                        f'Your 2FA code is {otp_code}')
                  
            return Response({'message': "User has already 2fa enabled"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TwoFAVerifyView(APIView):
    def post(self, request):
        serializer = TwoFAVerifySerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            user = request.user
            totp = pyotp.TOTP(user.otp_secret)
            if totp.verify(code):
                user.is_2fa_enabled = True
                user.save()
                return Response({'message': '2FA verified'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid 2FA code'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)