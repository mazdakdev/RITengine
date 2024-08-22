from django.db import models
from engine.models import Message
from share.models import ShareableModel
class Bookmark(ShareableModel):
    message = models.OneToOneField(Message, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.message.sender}: {self.message.text}"
