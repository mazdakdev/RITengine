from uuid import uuid4
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        email = data.get('email')

        if not email:
            raise ValidationError("Email is required to continue registration and nothing was provided by the provider.")

        user = sociallogin.user
        user.email = email

        provider = sociallogin.account.provider

        if provider == 'google':
            user.first_name = data.get('last_name', '')
            user.last_name = data.get('first_name', '')
            user.image = data.get('picture', '')

        elif provider == 'facebook':
            user.first_name = data.get('first_name', '')
            user.last_name = data.get('last_name', '')
            user.image = f"https://graph.facebook.com/{sociallogin.account.uid}/picture?type=large"

        elif provider == 'github':
            user.first_name = data.get('name', '').split()[0]
            user.last_name = data.get('name', '').split()[-1] if len(data.get('name', '').split()) > 1 else ''
            user.image = data.get('avatar_url', '')

        elif provider == 'apple':
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)

        username = data.get('username')
        if not username:
            username = email.split('@')[0]  # Use email prefix if no username is provided
            username = self.generate_unique_username(username)

        user.username = username

        return user

    def generate_unique_username(self, base_username):
        username = base_username

        # Ensure the username is unique
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{uuid4().hex[:6]}"

        return username
