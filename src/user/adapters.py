from uuid import uuid4

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.text import slugify

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        if not data.get('email'):
            raise ValidationError("Email is required to continue registration and nothing was provided by the provider.")

        user = sociallogin.user
        user.email = data.get('email')
        user.username = self.generate_unique_username(user.email)

        if data.get('name'):
            user.f_name = data.get('name').split()[0]
            user.l_name = data.get('name').split()[-1]

        return user

    def generate_unique_username(self, email):
        base_username = slugify(email.split('@')[0])
        username = base_username

        # Append a short UUID to ensure uniqueness
        while User.objects.filter(username=username).exists():
            unique_suffix = uuid4().hex[:6]
            username = f"{base_username}_{unique_suffix}"

        return username
