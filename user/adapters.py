from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
import random
import string

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = sociallogin.user
        user.email = data.get('email')
        user.first_name = data.get('name').split()[0]
        user.last_name = data.get('name').split()[-1]

        # Generate a username
        user.username = self.generate_unique_username(user.email)
        return user

    #TODO: this approach must be changed
    def generate_unique_username(self, email):
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        
        # Ensure the username is unique
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        
        return username