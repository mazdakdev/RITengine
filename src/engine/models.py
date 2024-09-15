from django.db import models, IntegrityError
from bookmark.models import Bookmark
from share.models import ShareableModel
from .factories import ExternalServiceFactory
import uuid

class Chat(ShareableModel):
    title = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = str(uuid.uuid4())
        super(Chat, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

class EngineCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    prompt = models.TextField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['is_default'],
                name='unique_default_engine_category',
                condition=models.Q(is_default=True)
            )
        ]

    def save(self, *args, **kwargs):
        """Ensure that only one default category exists"""
        if self.is_default:
            existing_default = EngineCategory.objects.filter(is_default=True).exclude(pk=self.pk).exists()
            if existing_default:
                raise IntegrityError('There can only be one default category.')

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Engine(models.Model):
    name = models.CharField(max_length=100)
    prompt = models.TextField(null=True, blank=True)
    category = models.ForeignKey(EngineCategory, related_name="engines", on_delete=models.CASCADE)
    EXTERNAL_SERVICE_CHOICES = (
        ('darkob', 'Darkob'),
    )
    external_service = models.CharField(max_length=255, choices=EXTERNAL_SERVICE_CHOICES, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_service_adapter(self):
        return ExternalServiceFactory.get_service_adapter(self.external_service)


class Message(models.Model):
    SENDER_CHOICES = (
        ('user', 'User'),
        ('engine', 'RIT-engine'),
    )
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    text = models.TextField()
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES, default='user')
    engines = models.ManyToManyField(Engine, related_name="messages")
    bookmark = models.ForeignKey(Bookmark, on_delete=models.SET_NULL, related_name='messages', null=True, blank=True)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_sender_display()}: {self.text[:50]}"

class Assist(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.ImageField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
