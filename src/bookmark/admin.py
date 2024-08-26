from django.contrib import admin
from .models import Bookmark

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Enforce singleton rule
        if Bookmark.objects.exists():
            return False
        return super().has_add_permission(request)
