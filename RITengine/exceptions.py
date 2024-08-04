from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler
from rest_framework import status

from RITengine.throttles import CustomThrottled


class CustomAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An unknown error occurred.'
    default_code = 'unknown_error'

    def __init__(self, detail=None, status_code=None, code=None, **kwargs):
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.default_code = code
        super().__init__(detail, code=self.default_code)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data['status'] = "error"

        # Attach the error code from the exception to the response
        if isinstance(exc, CustomAPIException):
            response.data['error_code'] = exc.default_code

        if isinstance(exc, ValidationError):
            response.data['error_code'] = "serializer_validation_errors"

        if isinstance(exc, CustomThrottled):
            response.data['error_code'] = 'rate_limit_exceeded'
            response.data['wait_time'] = int(exc.wait_time)

    return response
