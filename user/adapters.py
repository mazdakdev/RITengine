from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        if not data.get('email'):
            raise ValidationError("Email is required to continue registration and nothing was provided by the provider.")

        user = sociallogin.user
        user.email = data.get('email')
        user.username = self.generate_unique_username(user.email)

        if data.get('name'):
            user.fname = data.get('name').split()[0]
            user.lname = data.get('name').split()[-1]

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