from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class ShareableModel(models.Model):
    shareable_key = models.CharField(max_length=8, unique=True, editable=False, null=True, blank=True)
    viewers = models.ManyToManyField(User, related_name='%(class)s_viewers',  blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_%(class)ss')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.shareable_key:
            self.shareable_key = self.generate_shareable_key()
        super().save(*args, **kwargs)

    def generate_shareable_key(self):
        return uuid.uuid4().hex[:8]
