from .providers import SMSProvider

class SMSService:
    def __init__(self, provider: SMSProvider):
        self.provider = provider

    def send_otp(self, phone_number):
        return self.provider.send_otp(phone_number) 

    def send_message(self, phone_number, message):
        return self.provider.send_message(phone_number, message)