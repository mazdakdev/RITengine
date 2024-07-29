from RITengine.exceptions import CustomAPIException
from rest_framework import status

class InvalidCredentials(CustomAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid Credentials."
    default_code = "invalid_credentials"

class EmailNotVerified(CustomAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "User's E-mail is not yet verified."
    default_code = 'email_not_verified'


class InvalidTwoFaOrOtp(CustomAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid or Expired otp/two-fa code provided."
    default_code = 'invalid_otp_or_two_fa'


class TwoFaRequired(CustomAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED,
    default_detail = "Two-Factor code is required.",
    default_code = "two_fa_required",
