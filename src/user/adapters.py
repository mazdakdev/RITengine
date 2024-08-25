from uuid import uuid4
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.text import slugify

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        email = data.get('email')

        if not email:
            raise ValidationError("Email is required to continue registration and nothing was provided by the provider.")

        # Check if a user with this email already exists
        try:
            user = User.objects.get(email=email)
            sociallogin.user = user
            return user
        except User.DoesNotExist:
            # If the user doesn't exist, create a new one
            user = sociallogin.user
            user.email = email

            # Generate a username based on the provided data or email
            username = data.get('username')
            if username:
                user.username = self.generate_unique_username(username)
            else:
                user.username = self.generate_unique_username(email.split('@')[0])

            # Assign first and last name if provided by the provider
            if data.get('name'):
                name_parts = data.get('name').split()
                user.first_name = name_parts[0] if name_parts else ''
                user.last_name = name_parts[-1] if len(name_parts) > 1 else ''

            return user

    def generate_unique_username(self, base_username):
        username = base_username

        # Ensure the username is unique
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{uuid4().hex[:6]}"

        return username
