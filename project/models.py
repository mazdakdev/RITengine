from django.contrib.auth import get_user_model
from django.db import models
from engine.models import Message

class Project(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='assets/projects/', blank=True, null=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    messages = models.ManyToManyField(Message, related_name='projects', blank=True, null=True)