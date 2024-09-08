from django_otp.models import ThrottlingMixin, SideChannelDevice
from django_otp.plugins.otp_email.models import EmailDevice as _EmailDevice
from django.conf import settings
from django.db import models

class SMSDevice(ThrottlingMixin, SideChannelDevice):
    """
    Custom SMS Device that uses and handles the OTP generation using Celery.
    """

    number = models.CharField(
        max_length=30, help_text="The mobile number to deliver tokens to (E.164)."
    )

    class Meta(SideChannelDevice.Meta):
        verbose_name = "SMS Device"

    def get_throttle_factor(self):
        return getattr(settings, 'OTP_TWILIO_THROTTLE_FACTOR', 1)

    def generate_challenge(self) -> None:
        """
        Enqueues the current TOTP token to be sent to `self.number` via a Celery task.
        Sends a challenge to the user via service.
        """
        self.generate_token(valid_secs=getattr(settings, 'OTP_TWILIO_TOKEN_VALIDITY', 300))

        from .tasks import send_sms_otp_task
        send_sms_otp_task.delay(self.id, str(self.number))

        return "otp sent"

    def verify_token(self, token):
        verify_allowed, _ = self.verify_is_allowed()
        if verify_allowed:
            verified = super().verify_token(token)

            if verified:
                self.throttle_reset()
            else:
                self.throttle_increment()
        else:
            verified = False

        return verified


class EmailDevice(_EmailDevice):
    def _deliver_token(self, extra_context):
        from .tasks import send_email
        self.cooldown_set(commit=False)
        self.generate_token(valid_secs=300, commit=True)

        context = {'token': self.token, **(extra_context or {})}

        send_email.delay(
            subject="2FA code",
            template_name="emails/verification.html",
            recipient_email=[self.email or self.user.email],
            context=context
        )

        return "sent by email"