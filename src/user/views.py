from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
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
    CompletePasswordResetSerializer
)
from .throttles import TwoFAAnonRateThrottle, TwoFAUserRateThrottle
from rest_framework import generics
from django.db.models import Q


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


class CustomRegisterView(APIView):
    """
    Creates user obj and sends an otp
    """
    def post(self, request):
          serializer = RegistrationSerializer(data=request.data)
          serializer.is_valid(raise_exception=True)
          user = serializer.save(request)

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

    def partial_update(self, request, *args, **kwargs):
        if request.user.is_oauth_based:
            return Response(
                {
                    "status": "error",
                    "details": 'Method "PATCH" not allowed for OAuth-based users.',
                    "error_code": "oauth_restricted",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        required_fields = ["f_name", "l_name", "birthday"]

        current_data = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        for field in required_fields:
            if (
                field not in serializer.validated_data
                and getattr(current_data, field) is None
            ):
                # Required field is missing
                return Response(
                    {
                        "status": "error",
                        "details": f"The field {field} is required to be updated first.",
                        "error_code": "required_field_missing",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)



class PasswordResetView(APIView):
    permission_classes = [IsNotOAuthUser,]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Generate temporary token and bind it to the user ID
        tmp_token = utils.generate_tmp_token(user, "2fa")  # Implement this method
        cache.set(f"2fa_tmp_token_{user.id}", tmp_token, timeout=300)  # Cache the token for a limited time

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
        serializer.save()  # This will reset the user's password

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


class Request2FAView(APIView):
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    def post(self, request):
        serializer = Request2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if not user.preferred_2fa:
            otp, secret = utils.generate_otp()
            user.send_email("otp", otp.now())
            cache.set(f"otp_secret_{user.id}", secret, timeout=300)

            return Response(
                {"status": "success", "details": "an otp has been sent successfully."}
            )

        utils.generate_2fa_challenge(user)
        return Response(
            {"status": "success", "details": "a 2fa code has been sent successfully."}
        )


class Enable2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    def post(self, request):
        user = request.user
        serializer = Enable2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        method = serializer.validated_data["method"]
        device = getattr(user, f"{method}_device", None)

        if not user.preferred_2fa:
            if device is None or not device.confirmed:
                if method == "email":
                    device = EmailDevice(user=user, confirmed=False)
                elif method == "sms":
                    if not user.phone_number:
                        raise CustomAPIException("You have not set any phone number.")

                    device = SMSDevice(
                        user=user, number=user.phone_number, confirmed=False
                    )
                elif method == "totp":
                    device = TOTPDevice(user=user, step=60, confirmed=False)

                device.save()
                setattr(user, f"{method}_device", device)
                user.save()

                if method in ["email", "sms"]:
                    device.generate_challenge()
                    details = (
                        "An E-mail has been sent."
                        if method == "email"
                        else "An SMS has been sent."
                    )
                else:  # TOTP
                    details = {"provisioning_uri": device.config_url}

                return Response(
                    {
                        "status": "success",
                        "details": details,
                    },
                    status=status.HTTP_200_OK,
                )

        return Response(
            {
                "status": "error",
                "details": "2FA is already enabled or an unknown error occurred.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class Verify2FASetupView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]

    def post(self, request, *args, **kwargs):
        serializer = Verify2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = serializer.validated_data["method"]
        otp_code = serializer.validated_data["code"]
        user = request.user

        device = getattr(user, f"{method}_device", None)

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

                return Response(
                    {
                        "status": "success",
                        "details": "2FA setup completed.",
                        "backup_codes": backup_code_serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                raise exceptions.InvalidTwoFaOrOtp()

        else:
            raise exceptions.UnknownError()


class Disable2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    def post(self, request):
        user = request.user
        if not user.preferred_2fa:
            raise exceptions.No2FASetUp()

        if user.preferred_2fa == "totp":  # no need to generate challenge
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

        raise exceptions.UnknownError


class CompleteDisable2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    def post(self, request):
        user = request.user
        if not user.preferred_2fa:
            raise exceptions.No2FASetUp()

        serializer = CompleteDisable2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"]

        if not utils.validate_two_fa(user, code):
            raise exceptions.InvalidTwoFaOrOtp()

        method = user.preferred_2fa
        device = getattr(user, f"{user.preferred_2fa}_device", None)

        if device:
            user.preferred_2fa = None
            device.delete()
            setattr(user, f"{method}_device", None)
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

        otp, secret = utils.generate_otp()
        user.send_email("otp", otp.now())

        tmp_token = utils.generate_tmp_token(user, "email_change")
        cache.set(f"email_change_otp_{user.id}", secret, timeout=300)
        cache.set(f"email_change_email_{user.id}", new_email, timeout=300)

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
            raise exceptions.InvalidTmpToken

        try:
            otp_secret = cache.get(f"email_change_otp_{user.id}")
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

        cache.delete(f"email_change_otp_{user.id}")
        cache.delete(f"email_change_tmp_token_{user.id}")
        cache.delete(f"email_change_new_email_{user.id}")

        return Response(
            {
                "status": "success",
                "email": new_email,
            },
            status=status.HTTP_200_OK,
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


class UserSearchView(APIView):
    """
    Filter users based on their identifier (email, username, or phone number).
    Supports partial matches.
    """
    def get(self, request, *args, **kwargs):
        identifier = request.query_params.get('identifier', '').strip()

        if identifier:
            User = get_user_model()

            users = User.objects.filter(
                Q(email__icontains=identifier) |
                Q(username__icontains=identifier) |
                Q(phone_number__icontains=identifier)
            )

            if users.exists():
                serializer = UserSerializer(users, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                raise CustomAPIException("No users found with the given identifier.")

        raise CustomAPIException("Identifier is required.")


# TODO: Refactor password resets
# TODO: change 2fa method
# TODO: other social auths
# TODO: generate new sets backup codes & complete
# TODO: make all error messages better
# TODO: make otp/2fa expiration time dynamic
# TODO: deactive unverified email after ...
