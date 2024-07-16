from django.db import models
from django.contrib.auth import get_user_model
class Chat(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

class Message(models.Model):
    SENDER_CHOICES = (
        ('user', 'User'),
        ('engine', 'RIT-engine'),
    ) # TODO: different prompts

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    text = models.TextField()
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES, default='user')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_sender_display()}: {self.text[:50]}"

class Engine(models.Model):
    name = models.CharField(max_length=100)
    prompt = models.TextField()

    def __str__(self):
        return self.name
