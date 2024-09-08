from django.db import models
from share.models import ShareableModel
from RITengine.exceptions import CustomAPIException

class Bookmark(ShareableModel):
    """
    A singleton based bookmark collection (for now)
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk and Bookmark.objects.filter(user=self.user).exists():
            raise CustomAPIException(
                detail='Only one instance of Bookmark could exist for each user (singleton is enforced for now).'
            )
        return super(Bookmark, self).save(*args, **kwargs)
