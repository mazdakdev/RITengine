from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

@shared_task
def deactivate_inactive_users():
    one_week_ago = timezone.now() - timedelta(weeks=1)
    inactive_users = User.objects.filter(is_active=True, created_at__lte=one_week_ago)
    inactive_users.update(is_active=False)
