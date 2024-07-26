from django.db import models
from engine.models import Message
from share.models import ShareableModel

class Bookmark(ShareableModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.message.sender}: {self.message.text}"