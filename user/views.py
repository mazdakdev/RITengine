from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView, RegisterView
from django.core import cache
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter, OpenApiTypes
from dj_rest_auth.views import LoginView, UserDetailsView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from rest_framework.views import APIView
from  dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_email.models import EmailDevice
from .models import SMSDevice
from rest_framework.permissions import IsAuthenticated
import pyotp
from . import  utils
from .utils import generate_otp, get_jwt_token
from .permissions import IsNotOAuthUser
from .serializers import (
    Verify2FASerializer, Enable2FASerializer, Request2FASerializer,
    PasswordChangeSerializer, PasswordResetSerializer,
    CustomLoginSerializer,
    OTPSerializer,
    UserSerializer, CompleteLoginSerializer, CustomRegisterSerializer,
)


User = get_user_model()

@extend_schema(
    request=inline_serializer(name="GithubReqSerializer", fields={
        'access_token': serializers.CharField()
    }),
    description="Github's Oauth",
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
    request=RegisterSerializer,
)
class CustomRegisterView(RegisterView):
    serializer_class = CustomRegisterSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request)

        return Response({
            'status': "success",
            'details': 'Verification code sent successfully.'

        }, status=status.HTTP_200_OK)

@extend_schema(
    request=CustomLoginSerializer,
)
class CustomLoginView(LoginView):
    serializer_class = CustomLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        if user.preferred_2fa:
            tmp_token = utils.generate_tmp_token(user)
            utils.generate_2fa_challenge(user)

            return Response({
                    "status": "2fa_required",
                    "tmp_token": tmp_token
                },
                status=status.HTTP_202_ACCEPTED
            )


        access, refresh, access_exp, refresh_exp = get_jwt_token(user)
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


class CompleteLoginView(LoginView):
    serializer_class = CompleteLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        access, refresh, access_exp, refresh_exp = get_jwt_token(user)
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


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Bearer token for authentication',
            required=True,
        ),
        ],
)
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

@extend_schema(
    request=OTPSerializer,
)
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
                            access, refresh, access_exp, refresh_exp = get_jwt_token(user)
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
                                'error_code': 'error-invalid-value',
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
                    'status': '',
                    'details': 'Invalid email.',
                    'error_code': 'error-user-not-found'

                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'error',
            'details': serializer.errors,
            'error_code': 'error-serializer-validation'
        }, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=PasswordResetSerializer,
)
class PasswordResetView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()

        return Response({
            'status': 'success',
            'details': 'Password has been reset.'
        }, status=status.HTTP_200_OK)

@extend_schema(
    request=PasswordChangeSerializer,
    parameters=[
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Bearer token for authentication',
            required=True,
        ),
    ],
 )
class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    def post(self, request, *args, **kwargs):

        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['new_password1']
        user = request.user
        user.set_password(new_password)
        user.save()
        return Response({
            'status': 'success',
            'details': 'Password has been changed.'
        }, status=status.HTTP_200_OK)

@extend_schema(
    request=Request2FASerializer,
 )
class Request2FAView(APIView):
    permission_classes = [IsNotOAuthUser,]
    def post(self, request):
        serializer = Request2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
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
                "details": "an E-mail has been sent successfully to the user."
            })

        elif user.preferred_2fa == "sms":
            device = SMSDevice.objects.filter(user=user).first()
            device.generate_challenge()
            return Response({
                'status': 'success',
                "details": "an sms has been sent successfully to the user."
            })

        elif user.preferred_2fa == "totp":
            return Response({
                'status': 'error',
                "details": "No need to request 2FA for this user (CHECK THE AUTHENTICATOR APP).",
                'error_code': "error_2fa_request_totp"
            })



@extend_schema(
    request=Enable2FASerializer,
    parameters=[
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Bearer token for authentication',
            required=True,
        ),
    ],
 )
class Enable2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]

    def post(self, request):
        user = request.user
        serializer = Enable2FASerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        method = serializer.validated_data['method']

        if not user.preferred_2fa:

            if method == 'email':
                device = EmailDevice(user=user, confirmed=False)
                device.generate_challenge()

                return Response({
                    'status': 'success',
                    'details': 'an E-mail has been sent to the User.',
                }, status=status.HTTP_200_OK)

            elif method == 'sms':
                device = SMSDevice(user=user, number=user.phone_number, confirmed=False)
                device.generate_challenge()

                return Response({
                    'status': 'success',
                    'details': 'an SMS has been sent to the User.',
                }, status=status.HTTP_200_OK)


            elif method == 'totp':
                device = TOTPDevice.objects.create(user=user, confirmed=False)
                return Response({
                    'status': 'success',
                    'data':{
                        "provisioning_uri": device.config_url
                    }

                }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'details': 'User has already 2fa enabled.',
            'error': 'error-2fa-already-enabled'
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=Verify2FASerializer,
    parameters=[
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Bearer token for authentication',
            required=True,
        ),
    ],
 )
class Verify2FASetupView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]

    def post(self, request, *args, **kwargs):
        serializer = Verify2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = serializer.validated_data['method']
        otp_code = serializer.validated_data['otp']
        user = request.user

        if method == 'email':
            device = EmailDevice.objects.filter(user=user, confirmed=False).first()
        elif method == 'sms':
           device = SMSDevice.objects.filter(number=user.phone_number, confirmed=False).first()
        elif method == 'totp':
            device = TOTPDevice.objects.filter(user=user, confirmed=False).first()

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


#TODO: other social auths
#TODO: Twilio
#TODO: backup codes
#TODO: change 2fa method
