from .adapters import SMSAdapter, TwilioAdapter, MeliPayamakAdapter

class SMSAdapterFactory:
    @staticmethod
    def get_sms_adapter(provider_name: str) -> SMSAdapter:
        if provider_name == 'twilio':
            return TwilioAdapter()
        elif provider_name == 'melipayamak':
            return MeliPayamakAdapter()
        else:
            raise ValueError(f"Unknown OTP provider: {provider_name}")
