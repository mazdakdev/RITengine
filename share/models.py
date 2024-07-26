from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class ShareableModel(models.Model):
    shareable_key = models.UUIDField(unique=True, editable=False, null=True, blank=True)
    viewers = models.ManyToManyField(User, related_name='%(class)s_viewers',  blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_%(class)ss')

    class Meta:
        abstract = True

    def generate_shareable_key(self):
        if not self.shareable_key:
            self.shareable_key = uuid.uuid4()
            self.save()

            return self.shareable_key


class AccessRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    requested_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    approval_uuid = models.UUIDField(default=uuid.uuid4(), editable=False, unique=True)

