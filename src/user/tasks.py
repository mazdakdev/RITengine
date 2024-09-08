from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from tenacity import retry, wait_exponential, stop_after_attempt
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .factories import SMSAdapterFactory
from .otp_devices import SMSDevice
import requests
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
def send_sms_otp_task(device_id, phone_number):
    try:
        device = SMSDevice.objects.get(id=device_id)
        adapter = SMSAdapterFactory.get_sms_adapter(settings.SMS_PROVIDER)
        code = adapter.send_otp(phone_number)

        device.token = str(code)
        device.valid_until = timezone.now() + timedelta(seconds=300)
        device.save()

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error sending token via {settings.SMS_PROVIDER}: {e}")
        raise

@shared_task
def send_email(subject, template_name, recipient_email, context={}, from_email=settings.EMAIL_FROM):
    html_message = render_to_string(template_name, context)
    email = EmailMessage(
        subject,
        html_message,
        from_email,
        [recipient_email]
    )

    email.content_subtype = "html"
    email.send(fail_silently=False)


@shared_task
def send_text_email(subject, message, recipient_email, from_email=settings.EMAIL_FROM):
    email = EmailMessage(
        subject,
        message,
        from_email,
        [recipient_email]
    )
    email.send(fail_silently=False)
