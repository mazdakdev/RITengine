from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .utils import generate_otp

User = get_user_model()

@receiver(post_save, sender=User)
def send_otp_on_registration(sender, instance, created, **kwargs):
    if created:
        otp, secret = generate_otp()
        instance.send_email("otp", otp.now())
        instance.otp_secret = secret
        instance.save()