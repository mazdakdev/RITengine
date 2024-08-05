from django.db import models
from engine.models import Message
from share.models import ShareableModel


class Project(ShareableModel):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='assets/projects/', blank=True, null=True)
    messages = models.ManyToManyField(Message, related_name='projects', blank=True)

#TODO: others users must not be able to see other projects