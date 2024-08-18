from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .utils import generate_otp
from django.core.cache import cache

User = get_user_model()

@receiver(post_save, sender=User)
def send_otp_on_registration(sender, instance, created, **kwargs):
    if created:
        if not instance.is_staff:
            otp, secret = generate_otp()

            instance.send_email(
                subject=f"RITengine: {otp.now()}",
                template_name="emails/verification.html",
                context={"code": otp.now()}
            )
            cache.set(f"otp_secret_{instance.id}", secret, timeout=300)
        else:
            instance.is_email_verified = True
            instance.save()
