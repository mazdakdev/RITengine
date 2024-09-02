from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_email.models import EmailDevice
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from .models import SMSDevice, BackupCode
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
import pyotp
from . import utils
from .services import SMSService
from .providers import get_sms_provider
from .permissions import IsNotOAuthUser
from RITengine.exceptions import CustomAPIException
from rest_framework.exceptions import ValidationError
from . import exceptions
from .serializers import (
    Verify2FASerializer, Enable2FASerializer, Request2FASerializer,
    PasswordChangeSerializer, PasswordResetSerializer, LoginSerializer,
    CompleteRegisterationSerializer, UsernameChangeSerializer, UserSerializer,
    CompleteLoginSerializer, RegistrationSerializer, UserDetailsSerializer,
    BackupCodeSerializer, EmailChangeSerializer, CompleteEmailorPhoneChangeSerializer,
    PhoneChangeSerializer, CompleteDisable2FASerializer, CompletePasswordChangeSerializer,
    CompletePasswordResetSerializer, Change2FAMethodSerializer
)
from .throttles import TwoFAAnonRateThrottle, TwoFAUserRateThrottle
from rest_framework import generics
from django.db.models import Q


User = get_user_model()


class GitHubLoginView(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = f"{settings.OAUTH_BASE_CALLBACK_URL}/github"
    client_class = OAuth2Client

    def process_login(self):
        super().process_login()
        self.request.user.is_email_verified = True
        self.request.user.is_oauth_based = True
        self.request.user.save()

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user)
        access, refresh, access_exp, refresh_exp = utils.get_jwt_token(user)
        return Response(
            {
                "access": str(access),
                "refresh": str(refresh),
                "access_expiration": access_exp,
                "refresh_expiration": refresh_exp,
                "user": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = f"{settings.OAUTH_BASE_CALLBACK_URL}/google"
    client_class = OAuth2Client

    def process_login(self):
        super().process_login()
        self.request.user.is_email_verified = True
        self.request.user.is_oauth_based = True
        self.request.user.save()

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user)
        access, refresh, access_exp, refresh_exp = utils.get_jwt_token(user)
        return Response(
            {
                "access": str(access),
                "refresh": str(refresh),
                "access_expiration": access_exp,
                "refresh_expiration": refresh_exp,
                "user": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class CustomRegisterView(APIView):
    """
    Creates user obj and sends an otp
    """
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request)

        return Response(
            {"status": "success", "details": "Verification code sent successfully."},
            status=status.HTTP_200_OK,
        )

class CompleteRegistrationView(APIView):
    """
    Verifies the otp and hence the user's registertaion
    """
    def post(self, request):
        serializer = CompleteRegisterationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.send_email(
                subject=f"Welcome to RITengine",
                template_name="emails/welcome.html",
            )

        access, refresh, access_exp, refresh_exp = utils.get_jwt_token(user)
        user_serializer = UserSerializer(user)

        return Response(
            {
                # 'status': "success",
                # 'data': {
                "access": str(access),
                "refresh": str(refresh),
                "access_expiration": access_exp,
                "refresh_expiration": refresh_exp,
                "user": user_serializer.data,
                # }
            },
            status=status.HTTP_200_OK,
        )


class CustomLoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if user.preferred_2fa:
            tmp_token = utils.generate_tmp_token(user, "2fa")
            utils.generate_2fa_challenge(user)

            return Response(
                {"status": "2fa_required", "tmp_token": tmp_token},
                status=status.HTTP_202_ACCEPTED,
            )

        user.last_login = timezone.now()
        user.save()
        access, refresh, access_exp, refresh_exp = utils.get_jwt_token(user)
        user_serializer = UserSerializer(user)

        return Response(
            {
                "access": str(access),
                "refresh": str(refresh),
                "access_expiration": access_exp,
                "refresh_expiration": refresh_exp,
                "user": user_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class CompleteLoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CompleteLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        user.last_login = timezone.now()
        user.save()
        access, refresh, access_exp, refresh_exp = utils.get_jwt_token(user)
        user_serializer = UserSerializer(user)

        return Response(
            {
                "access": str(access),
                "refresh": str(refresh),
                "access_expiration": access_exp,
                "refresh_expiration": refresh_exp,
                "user": user_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class UserDetailsView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailsSerializer

    def get_object(self):
        return self.request.user

    # def partial_update(self, request, *args, **kwargs):
    #     required_fields = ["first_name", "last_name", "birthday"]

    #     current_data = self.get_object()
    #     serializer = self.get_serializer(data=request.data, partial=True)
    #     serializer.is_valid(raise_exception=True)

    #     for field in required_fields:
    #         if (
    #             field not in serializer.validated_data
    #             and getattr(current_data, field) is None
    #         ):
    #             # Required field is missing
    #             return Response(
    #                 {
    #                     "status": "error",
    #                     "details": f"The field {field} is required to be updated first.",
    #                     "error_code": "required_field_missing",
    #                 },
    #                 status=status.HTTP_400_BAD_REQUEST,
    #             )

    #     user = self.get_object()
    #     serializer = self.get_serializer(user, data=request.data, partial=True)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_update(serializer)

    #     return Response(serializer.data)



class PasswordResetView(APIView):
    permission_classes = [IsNotOAuthUser,]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Generate temporary token and bind it to the user ID
        tmp_token = utils.generate_tmp_token(user, "passwd")

        return Response(
            {
                "status": "verification_required",
                "tmp_token": tmp_token
            },
            status=status.HTTP_202_ACCEPTED,
        )

class CompletePasswordResetView(APIView):
    permission_classes = [IsNotOAuthUser,]

    def post(self, request):
        serializer = CompletePasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"status": "success", "message": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]

    def post(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            {"status": "verification_required",},
            status=status.HTTP_202_ACCEPTED,
        )

class CompletePasswordChangeView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]

    def post(self , request, *args, **kwargs):
        serializer = CompletePasswordChangeSerializer(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "status": "success",
                "details":"Password changed successfully"
            },
            status=status.HTTP_200_OK,
        )

class Enable2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    def post(self, request):
        user = request.user
        serializer = Enable2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = serializer.validated_data["method"]

        for device_type in ['email_device', 'sms_device', 'totp_device']:
            device = getattr(user, device_type, None)
            if device and not device.confirmed:
                device.delete()
                setattr(user, device_type, None)

        device = getattr(user, f"{method}_device", None)
        if device and device.confirmed:
            return Response({
                "status": "error",
                "details": f"{method.capitalize()} 2FA is already enabled.",
            }, status=status.HTTP_400_BAD_REQUEST)

        device = utils.create_device(user, method)
        device.save()
        setattr(user, f"{method}_device", device)
        user.save()

        response_data = {"status": "success"}
        if method in ["email", "sms"]:
            device.generate_challenge()
            response_data["details"] = "An email has been sent." if method == "email" else "An SMS has been sent."
        else:
            response_data["provisioning_uri"] = device.config_url

        return Response(response_data, status=status.HTTP_200_OK)

class Verify2FASetupView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]

    def post(self, request, *args, **kwargs):
        serializer = Verify2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = serializer.validated_data["method"]
        otp_code = serializer.validated_data["code"]
        user = request.user

        device = getattr(user, f"{method}_device", None)

        if device and device.verify_token(otp_code):
            with transaction.atomic():
                device.confirmed = True
                device.save()

                user.preferred_2fa = method
                user.save()

                for other_method in ['email', 'sms', 'totp']:
                    if other_method != method:
                        other_device = getattr(user, f"{other_method}_device", None)
                        if other_device:
                            other_device.delete()

                codes = utils.generate_backup_codes()
                backup_codes = [BackupCode(user=user, code=code) for code in codes]
                BackupCode.objects.bulk_create(backup_codes)

            backup_code_serializer = BackupCodeSerializer(backup_codes, many=True)

            return Response(
                {
                    "status": "success",
                    "details": "2FA setup completed.",
                    "backup_codes": backup_code_serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        else:
            raise InvalidTwoFaOrOtp()

class Change2FAMethodView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    def post(self, request):
        user = request.user
        serializer = Change2FAMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_method = serializer.validated_data["new_method"]
        new_device = getattr(user, f"{new_method}_device", None)

        if new_device is None or not new_device.confirmed:
            new_device = utils.create_device(user, new_method)
            new_device.save()
            setattr(user, f"{new_method}_device", new_device)
            user.save()

            response_data = {"status": "success"}
            if new_method in ["email", "sms"]:
                new_device.generate_challenge()
                response_data["details"] = "An email has been sent." if new_method == "email" else "An SMS has been sent."
            else:
                response_data["provisioning_uri"] = new_device.config_url

            return Response(response_data, status=status.HTTP_200_OK)

        user.preferred_2fa = new_method
        user.save()

        return Response(
            {
                "status": "success",
                "details": "2FA method updated successfully.",
            },
            status=status.HTTP_200_OK,
        )

class Disable2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    def post(self, request):
        user = request.user
        if not user.preferred_2fa:
            raise No2FASetUp()

        if user.preferred_2fa == "totp":
            return Response(
                {
                    "status": "verification_required",
                },
                status=status.HTTP_202_ACCEPTED,
            )

        device = getattr(user, f"{user.preferred_2fa}_device", None)

        if device:
            device.generate_challenge()
            return Response(
                {
                    "status": "verification_required",
                },
                status=status.HTTP_202_ACCEPTED,
            )

        raise UnknownError

class CompleteDisable2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    def post(self, request):
        user = request.user
        if not user.preferred_2fa:
            raise No2FASetUp()

        serializer = CompleteDisable2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"]

        if not utils.validate_two_fa(user, code):
            raise InvalidTwoFaOrOtp()

        method = user.preferred_2fa
        device = getattr(user, f"{user.preferred_2fa}_device", None)

        if device:
            with transaction.atomic():
                device.delete()
                setattr(user, f"{method}_device", None)
                user.preferred_2fa = None
                user.save()
                BackupCode.objects.filter(user=user).delete()

        return Response(
            {"status": "success", "details": "2FA has been disabled."},
            status=status.HTTP_200_OK,
        )


class UsernameChangeView(generics.UpdateAPIView):
    permission_class = [IsAuthenticated, IsNotOAuthUser]
    serializer_class = UsernameChangeSerializer

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        user = self.get_object()
        new_username = serializer.validated_data.get("username")
        user.username = new_username
        user.username_change_count += 1
        user.save()

        return user

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        user = self.get_object()
        remaining_changes = (
            settings.MAXIMUM_ALLOWED_USERNAME_CHANGE - user.username_change_count
        )
        response.data["remaining_changes"] = remaining_changes
        return response


class EmailChangeView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]

    def post(self, request, *args, **kwargs):
        serializer = EmailChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_email = serializer.validated_data.get("new_email")
        user = request.user

        utils.generate_and_send_otp(user)

        tmp_token = utils.generate_tmp_token(user, "email_change")
        cache.set(f"email_change_new_email_{user.id}", new_email, timeout=300)

        return Response(
            {"status": "verification_required", "tmp_token": tmp_token},
            status=status.HTTP_202_ACCEPTED,
        )


class CompleteEmailChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CompleteEmailorPhoneChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tmp_token = serializer.validated_data.get("tmp_token")
        code = serializer.validated_data.get("code")
        user = request.user

        cached_tmp_token = cache.get(f"email_change_tmp_token_{user.id}")
        if cached_tmp_token != tmp_token:
            raise exceptions.InvalidTmpToken()

        try:
            otp_secret = cache.get(f"otp_secret_{user.id}")
            totp = pyotp.TOTP(otp_secret, interval=300)
        except Exception:
            raise exceptions.UnknownError()

        if not totp.verify(code):
            raise exceptions.InvalidTwoFaOrOtp()

        new_email = cache.get(f"email_change_new_email_{user.id}")
        if not new_email:
            raise exceptions.UnknownError()

        user.email = new_email
        user.save()

        cache.delete(f"otp_secret_{user.id}")
        cache.delete(f"email_change_tmp_token_{user.id}")
        cache.delete(f"email_change_new_email_{user.id}")

        return Response({
            "status": "success",
            "email": new_email,
            }, status=status.HTTP_200_OK
        )


class PhoneChangeView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]

    def post(self, request, *args, **kwargs):
        serializer = PhoneChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_phone = serializer.validated_data.get("new_phone")
        user = request.user

        if new_phone == user.phone_number:
            raise CustomAPIException(
                "Your previous phone number can't be same with the new one.",
                status_code=400,
            )

        sms_service = SMSService(get_sms_provider(settings.SMS_PROVIDER))
        otp = sms_service.send_otp(phone_number=new_phone)

        tmp_token = utils.generate_tmp_token(user, "phone_change")
        cache.set(f"phone_change_otp_{user.id}", otp, timeout=300)
        cache.set(f"phone_change_new_phone_{user.id}", new_phone, timeout=300)

        return Response(
            {"status": "verification_required", "tmp_token": tmp_token},
            status=status.HTTP_202_ACCEPTED,
        )


class CompletePhoneChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CompleteEmailorPhoneChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tmp_token = serializer.validated_data.get("tmp_token")
        code = serializer.validated_data.get("code")
        user = request.user

        cached_tmp_token = cache.get(f"phone_change_tmp_token_{user.id}")
        if cached_tmp_token != tmp_token:
            raise exceptions.InvalidTmpToken()
        try:
            otp = cache.get(f"phone_change_otp_{user.id}")
        except Exception:
            raise exceptions.UnknownError()

        if otp != code:
            raise exceptions.InvalidTwoFaOrOtp()

        new_phone = cache.get(f"phone_change_new_phone_{user.id}")
        if not new_phone:
            raise CustomAPIException(
                detail="New Phone not found. try again from the initial step.",
                status_code=401,
            )
        user.phone_number = new_phone
        user.save()

        cache.delete(f"phone_change_otp_{user.id}")
        cache.delete(f"phone_change_tmp_token_{user.id}")
        cache.delete(f"phone_change_new_phone_{user.id}")

        return Response(
            {"status": "success", "phone": str(new_phone)}, status=status.HTTP_200_OK
        )


class UserGetView(APIView):
    """
    Retrieve a user based on their exact identifier (email, username, or phone number).
    """
    def get(self, request, *args, **kwargs):
        identifier = request.query_params.get('identifier', '').strip()

        if identifier:
            User = get_user_model()

            try:
                user = User.objects.get(
                    Q(email__iexact=identifier) |
                    Q(username__iexact=identifier) |
                    Q(phone_number__iexact=identifier)
                )

                serializer = UserSerializer(user)
                return Response(serializer.data, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                raise CustomAPIException("No user found with the given identifier.", status_code=status.HTTP_404_NOT_FOUND)

        raise CustomAPIException("Identifier is required.", status_code=status.HTTP_400_BAD_REQUEST)

# make 2fa change verify endpoint better
# TODO: other social auths
# TODO: generate new sets backup codes & complete
# TODO: make all error messages better
# TODO: make otp/2fa expiration time dynamic
# TODO: deactive unverified email after ...
