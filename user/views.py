from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView, RegisterView
from dj_rest_auth.views import UserDetailsView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_email.models import EmailDevice
from .models import SMSDevice, BackupCode
from rest_framework.permissions import IsAuthenticated
import pyotp
from . import utils
from .permissions import IsNotOAuthUser
from .serializers import (
    Verify2FASerializer, Enable2FASerializer, Request2FASerializer,
    PasswordChangeSerializer, PasswordResetSerializer,
    LoginSerializer,
    CompleteRegisterSerializer,
    UserSerializer, CompleteLoginSerializer, CustomRegisterSerializer,
    UserDetailSerializer, BackupCodeSerializer
)
from .throttles import TwoFAAnonRateThrottle

User = get_user_model()


class GitHubLoginView(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = "https://127.0.0.1:3000/oath/callback/github"
    client_class = OAuth2Client

    def process_login(self):
        super().process_login()
        self.request.user.is_email_verified = True
        self.request.user.is_oauth_based = True
        self.request.user.save()

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

class CompleteRegistrationView(APIView):
    def post(self, request):
        serializer = CompleteRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

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
                        access, refresh, access_exp, refresh_exp = utils.get_jwt_token(user)
                        user_serializer = UserSerializer(user)

                        return Response({
                            # 'status': "success",
                            # 'data': {
                            'access': str(access),
                            'refresh': str(refresh),
                            'access_expiration': access_exp,
                            'refresh_expiration': refresh_exp,
                            'user': user_serializer.data,

                            # }
                        }, status=status.HTTP_200_OK)

                    else:
                        return Response({
                            'status': 'error',
                            'details': 'Invalid or Expired otp/two-fa code provided.',
                            'error_code': 'invalid_otp_or_two_fa',
                        }, status=status.HTTP_401_UNAUTHORIZED)
                else:
                    return Response({
                        'status': 'error',
                        'details': "something went wrong, please try again.",
                        'error_code': 'otp_secret_not_found'
                    }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': 'error',
                'details': "User's email has already been verified.",
            }, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'details': 'Invalid Credentials.',
                'error_code': 'invalid_credentials'

            }, status=status.HTTP_400_BAD_REQUEST)

class CustomLoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
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

        access, refresh, access_exp, refresh_exp = utils.get_jwt_token(user)
        user_serializer = UserSerializer(user)

        return Response({
            'access': str(access),
            'refresh': str(refresh),
            'access_expiration': access_exp,
            'refresh_expiration': refresh_exp,
            'user': user_serializer.data,            
        }, status=status.HTTP_200_OK)


class CompleteLoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CompleteLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        access, refresh, access_exp, refresh_exp = utils.get_jwt_token(user)
        user_serializer = UserSerializer(user)

        return Response({
            'access': str(access),
            'refresh': str(refresh),
            'access_expiration': access_exp,
            'refresh_expiration': refresh_exp,
            'user': user_serializer.data,
        }, status=status.HTTP_200_OK)


class CustomUserDetailsView(UserDetailsView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer

    def update(self, request, *args, **kwargs):
        if request.user.is_oauth_based:
            return Response({
                'status': 'error',
                'details': 'Method "PUT" not allowed for OAuth-based users.',
                'error_code': 'oauth_restricted'
            }, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user.is_oauth_based:
            return Response({
                'status': 'error',
                'details': 'Method "PATCH" not allowed for OAuth-based users.',
                'error_code': 'oauth_restricted'
            }, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)


class PasswordResetView(APIView):
    permission_classes = [IsNotOAuthUser]
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


class Request2FAView(APIView):
    permission_classes = [IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle]
    def post(self, request):
        serializer = Request2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if not user.preferred_2fa:
            otp, secret = utils.generate_otp()
            user.send_mail("otp", otp.now())
            user.otp_secret = secret
            user.save()
            return Response({
                'status': 'success',
                "details": "an otp has been sent successfully."
            })


        utils.generate_2fa_challenge(user)
        return Response({
            'status': 'success',
            "details": "a 2fa code has been sent successfully."
        })


class Enable2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle]

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
                    'details': 'an E-mail has been sent.',
                }, status=status.HTTP_200_OK)

            elif method == 'sms':
                device = SMSDevice(user=user, number=user.phone_number, confirmed=False)
                device.generate_challenge()

                return Response({
                    'status': 'success',
                    'details': 'an SMS has been sent..',
                }, status=status.HTTP_200_OK)


            elif method == 'totp':
                device = TOTPDevice.objects.create(user=user, confirmed=False)
                return Response({
                    'status': 'success',
                    'data': {
                        "provisioning_uri": device.config_url
                    }

                }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'details': '2FA is already enabled.',
            'error': 'error-2fa-already-enabled'
        }, status=status.HTTP_400_BAD_REQUEST)


class Verify2FASetupView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]

    def post(self, request, *args, **kwargs):
        serializer = Verify2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = serializer.validated_data['method']
        otp_code = serializer.validated_data['code']
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
                codes = utils.generate_backup_codes()
                backup_codes = [BackupCode(user=user, code=code) for code in codes]
                BackupCode.objects.bulk_create(backup_codes)
                backup_code_serializer = BackupCodeSerializer(backup_codes, many=True)

                return Response({
                    'status': 'success',
                    'details': '2FA setup completed.',
                    "backup_codes": backup_code_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                'status': 'error',
                'details': 'Invalid or Expired otp/two-fa code provided.',
                'error_code': 'invalid_otp_or_two_fa',
            }, status=status.HTTP_401_UNAUTHORIZED)

        else:
            return Response({
                'status': 'error',
                'details': 'Device not found.',
                'error_code': 'error-2fa-device'

            }, status=status.HTTP_400_BAD_REQUEST)

class Disable2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle]

    def post(self, request):
        user = request.user
        if not user.preferred_2fa:
           return Response(
               {
                   'status': 'error',
                   'details': 'There is no two-factor setup for this user.',
                   'error': 'two_fa_not_set_up'
               }, status=status.HTTP_400_BAD_REQUEST
           )

        if not utils.validate_two_fa(user, self.request.data['code']):
            return Response({
                'status': 'error',
                'details': 'Invalid or Expired otp/two-fa code provided.',
                'error_code': 'invalid_otp_or_two_fa',
            }, status=status.HTTP_401_UNAUTHORIZED)

        user.preferred_2fa = None
        user.save()
        BackupCode.objects.filter(user=user).delete()
        return Response(
            {
                "status": "success",
                "details": "2FA has been disabled."
            },
            status=status.HTTP_200_OK
        )




#TODO: change 2fa method
#TODO: other social auths
#TODO: search
#TODO: generate new sets backup codes

#TODO: separate settings.py
#TODO: totp security check
#TODO: Deploy
