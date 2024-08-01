from django.contrib.contenttypes.models import ContentType
from django.db import models
from share.models import ShareableModel
from django.utils.text import slugify

class Chat(ShareableModel):
    title = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['created_at']
        unique_together = ('user', 'slug')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)

            unique_slug = self.slug
            num = 1
            while Chat.objects.filter(user=self.user, slug=unique_slug).exists():
                unique_slug = f"{self.slug}-{num}"
                num += 1
            self.slug = unique_slug
        super(Chat, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

class Message(models.Model):
    SENDER_CHOICES = (
        ('user', 'User'),
        ('engine', 'RIT-engine'),
    ) #IDEA: different prompts

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    text = models.TextField()
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES, default='user')

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_sender_display()}: {self.text[:50]}"

class Engine(models.Model):
    name = models.CharField(max_length=100)
    prompt = models.TextField()

    def __str__(self):
        return self.name


class Assist(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.ImageField(blank=True, null=True)

    def __str__(self):
        return self.name

