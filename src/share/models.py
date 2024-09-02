from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth import get_user_model
import uuid
import binascii

User = get_user_model()

class ShareableModel(models.Model):
    id = models.CharField(max_length=6, primary_key=True, editable=False)
    shareable_key = models.UUIDField(unique=True, editable=False, null=True, blank=True)
    viewers = models.ManyToManyField(User, related_name='%(class)s_viewers',  blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_%(class)ss')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.generate_hex_pk()
        super().save(*args, **kwargs)

    def generate_hex_pk(self):
        return binascii.b2a_hex(uuid.uuid4().bytes[:3]).decode().upper()

    def generate_shareable_key(self):
        if not self.shareable_key:
            self.shareable_key = uuid.uuid4()
            self.save()

            return self.shareable_key

class AccessRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=6)
    content_object = GenericForeignKey('content_type', 'object_id')
    requested_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    approval_uuid = models.UUIDField(editable=False, unique=True)


    def save(self, *args, **kwargs):
        if not self.approval_uuid:
            self.approval_uuid = uuid.uuid4()
        super().save(*args, **kwargs)
