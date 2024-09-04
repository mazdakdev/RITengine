from uuid import uuid4
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from abc import ABC, abstractmethod
from django.conf import settings
from rest_framework.exceptions import APIException
import logging
import requests

logger = logging.getLogger(__name__)

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
        User = get_user_model()

        # Ensure the username is unique
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{uuid4().hex[:6]}"

        return username

class SMSAdapter(ABC):
    @abstractmethod
    def send_otp(self, phone_number):
        pass

    @abstractmethod
    def send_message(self, phone_number, message):
        pass

class TwilioAdapter(SMSAdapter):
    def send_otp(self, phone_number):
       raise NotImplementedError()

class MeliPayamakAdapter(SMSAdapter):
    def send_otp(self, phone_number):
        data = {"to": str(phone_number)}
        response = requests.post(
            'https://console.melipayamak.com/api/send/otp/' + settings.MELI_PAYAMAK_KEY
            , json=data
        )

        if response.status_code == 200:
            return response.json()['code']

        else:
            logger.error('Error sending token by : {0}'.format(str(response.json()['status'])))
            raise APIException(detail="Error sending OTP by the provider, Please try again later.")

    def send_message(self, phone_number, message):
        raise NotImplementedError()
