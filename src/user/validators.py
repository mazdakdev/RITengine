from rest_framework.validators import ValidationError
from django.core.validators import RegexValidator

def no_spaces_validator(value):
    if " " in value:
        raise ValidationError("Username must not contain spaces.")

username_regex = RegexValidator(
        regex=r"^(?!\d)[^\@]*$",
        message="username must not start with numeric values nor contains any special chars other than _",
    )
