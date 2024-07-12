from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView, RegisterView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from dj_rest_auth.views import LoginView, UserDetailsView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_email.models import EmailDevice
from rest_framework.permissions import IsAuthenticated
from .api_docs import *
import pyotp
from .utils import generate_otp, get_jwt_token
from .permissions import IsNotOAuthUser
from datetime import datetime

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
        self.request.user.is_email_verified = True
        self.request.user.is_oauth_based = True
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
            return Response({
                'status': "success",
                'details': 'Verification code sent successfully.'

            }, status=status.HTTP_200_OK)
        return Response({
            'status': 'error',
            'details': {serializer.errors},
            'error_code': "error-serializer-validation"
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=CustomRegisterSerializer,
    responses={200: CustomLoginResponseSerializer}
)
class CustomLoginView(LoginView):
    serializer_class = CustomLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        access, refresh, access_exp, refresh_exp = get_jwt_token()
        user_serializer = UserSerializer(user)

        return Response({
            'status': "success",
            'data': {
                'access': str(access),
                'refresh': str(refresh),
                'access_expiration': access_exp,
                'refresh_expiration': refresh_exp,
                'user': user_serializer.data,

            }
        }, status=status.HTTP_200_OK)


class CustomUserDetailsView(UserDetailsView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def update(self, request, *args, **kwargs):
        if request.user.is_oauth_based:
            return Response({
                'status': 'error',
                'details': 'Method "PUT" not allowed for OAuth-based users.',
                'error_code': 'error-oauth-restricted'
            }, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user.is_oauth_based:
            return Response({
                'status': 'error',
                'details': 'Method "PATCH" not allowed for OAuth-based users.',
                'error_code': 'error-oauth-restricted'
            }, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

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
                            access, refresh, access_exp, refresh_exp = get_jwt_token()
                            access_token = refresh.access_token
                            user_serializer = UserSerializer(user)

                            return Response({
                                'status': "success",
                                'data': {
                                    'access': str(access),
                                    'refresh': str(refresh),
                                    'access_expiration': access_exp,
                                    'refresh_expiration': refresh_exp,
                                    'user': user_serializer.data,

                                }
                            }, status=status.HTTP_200_OK)

                        else:
                            return Response({
                                'status': 'error',
                                'details': 'Invalid OTP.',
                                'error_code': 'error-invalid-otp',
                            }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({
                            'status': 'error',
                            'details': 'User OTP Secret not found.',
                            'error_code': 'error-otp-secret-404'
                        }, status=status.HTTP_400_BAD_REQUEST)

                return Response({
                    'status': 'error',
                    'details': "User's email has already been verified.",
                    'error_code': 'error-user-already-verified'
                })

            except User.DoesNotExist:
                return Response({
                    'status': 'success',
                    'details': 'Invalid email.',
                    'error_code': 'error-user-not-found'

                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'error',
            'details': serializer.errors,
            'error_code': 'error-serializer-validation'
        }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            user.save()
            return Response({
                'status': 'success',
                'details': 'Password has been reset.'
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'details': serializer.errors,
            'error_code': 'error-serializer-validation'
        }, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    def post(self, request, *args, **kwargs):

        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            new_password = serializer.validated_data['new_password1']
            user = request.user
            user.set_password(new_password)
            user.save()
            return Response({
                'status': 'success',
                'details': 'Password has been changed.'
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'details': serializer.errors,
            'error_code': 'error-serializer-validation'
        }, status=status.HTTP_400_BAD_REQUEST)


class Request2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    def post(self, request):
        serializer = Request2FASerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            if not user.preferred_2fa:
                otp, secret = generate_otp()
                user.send_mail("otp", otp.now())
                user.otp_secret = secret
                user.save()
                return Response({
                    'status': 'success',
                    "details": "an otp has been sent successfully to the user."
                })

            if user.preferred_2fa == "email":
                device = EmailDevice.objects.filter(user=user).first()
                device.generate_challenge()
                return Response({
                    'status': 'success',
                    "message": "an E-mail has been sent successfully to the user."
                })

            elif user.preferred_2fa == "phone":
                pass

            elif user.preferred_2fa == "totp":
                return Response({
                    'status': 'error',
                    "details": "No need to request 2FA for this user (CHECK THE AUTHENTICATOR APP).",
                    'error_code': "error_2fa_request_totp"
                })

        return Response({
            'status': 'error',
            'details': serializer.errors,
            'error_code': 'error-serializer-validation'
        }, status=status.HTTP_400_BAD_REQUEST)


class Enable2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]

    def post(self, request):
        user = request.user
        method = request.data.get('method')

        if not user.preferred_2fa:

            if method == 'email':
                device = EmailDevice(user=request.user, confirmed=False)
                device.generate_challenge()
                # user.send_mail("2fa verification", otp_code)
                return Response({
                    'status': 'success',
                    'details': 'an E-mail has been sent to the User.',
                }, status=status.HTTP_200_OK)

            elif method == 'sms':
                pass
                # device = TwilioSMSDevice(user=request.user, confirmed=False)
                # otp_code = device.generate_challenge()
                # user.send_sms()

            elif method == 'totp':
                device = TOTPDevice.objects.create(user=user, confirmed=False)
                return Response({
                    'status': 'success',
                    'data':{
                        "provisioning_uri": device.config_url
                    }

                }, status=status.HTTP_200_OK)

            else:
                return Response({
                    'status': 'error',
                    'details': 'Invalid or not provided method.',
                    'error_code': 'error-invalid-2fa-method'
                }, status=status.HTTP_400_BAD_REQUEST)

            # return Response({'message': '2FA setup initiated. Please verify to complete.'}, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'details': 'User has already 2fa enabled.',
            'error': 'error-2fa-already-enabled'
        }, status=status.HTTP_400_BAD_REQUEST)


class Verify2FASetupView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]

    def post(self, request, *args, **kwargs):
        method = request.data.get('method')
        otp_code = request.data.get('otp')
        user = request.user

        if method == 'email':
            device = EmailDevice.objects.filter(user=request.user, confirmed=False).first()
        elif method == 'sms':
            # device = TwilioSMSDevice.objects.filter(user=request.user, confirmed=False).first()
            pass
        elif method == 'totp':
            device = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
        else:
            return Response({
                'status': 'error',
                'details': 'Invalid method.',
                'error_code': 'error-invalid-2fa-method'
            }, status=status.HTTP_400_BAD_REQUEST)

        if device:
            if device.verify_token(otp_code):
                device.confirmed = True
                device.save()
                user.preferred_2fa = method
                user.save()
                return Response({
                    'status': 'success',
                    'details': '2FA setup completed.'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'error',
                    'details': 'Invalid OTP code.',
                    'error_code': 'error-invalid-otp'

                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'status': 'error',
                'details': 'Device not found.',
                'error_code': 'error-2fa-device-404'

            }, status=status.HTTP_400_BAD_REQUEST)


#TODO: Docs (HIGH-PRIORITY) .
#TODO: other social auths (HIGH-PRIORITY)

# -------------------

#TODO: Twilio (LOW-PRIORITY)
#TODO: backup codes (LOW-PRIORITY)
#TODO: change 2fa method (LOW-PRIORITY)
#TODO: Too many Duplicate code in serializers.py
