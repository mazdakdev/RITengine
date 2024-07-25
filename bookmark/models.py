from django.db import models
from django.contrib.auth import get_user_model
from engine.models import Message

class Bookmark(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.message.sender}: {self.message.text}"