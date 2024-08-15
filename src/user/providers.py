from abc import ABC, abstractmethod
from django.conf import settings
from rest_framework.exceptions import APIException
import logging
import requests

logger = logging.getLogger(__name__)

class SMSProvider(ABC):
    @abstractmethod
    def send_otp(self, phone_number):
        pass

    @abstractmethod
    def send_message(self, phone_number, message):
        pass

class TwilioProvider(SMSProvider):
    def send_otp(self, phone_number):
       raise NotImplementedError()

class MeliPayamakProvider(SMSProvider):
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


def get_sms_provider(provider_name: str):
    if provider_name == 'twilio':
        pass
    elif provider_name == 'melipayamak':
        return MeliPayamakProvider()
    else:
        raise ValueError("Unknown OTP provider")             