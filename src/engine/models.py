from django.contrib.contenttypes.models import ContentType
from django.db import models
from bookmark.models import Bookmark
from share.models import ShareableModel
import uuid

class Chat(ShareableModel):
    title = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = str(uuid.uuid4())
        super(Chat, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


class Message(models.Model):
    SENDER_CHOICES = (
        ('user', 'User'),
        ('engine', 'RIT-engine'),
    )
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    text = models.TextField()
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES, default='user')
    bookmark = models.ForeignKey(Bookmark, on_delete=models.SET_NULL, related_name='messages', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_sender_display()}: {self.text[:50]}"

class EngineCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    prompt = models.TextField()

    def __str__(self):
        return self.name

class Engine(models.Model):
    name = models.CharField(max_length=100)
    prompt = models.TextField()
    category = models.ForeignKey(EngineCategory, related_name="engines", on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Assist(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.ImageField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
