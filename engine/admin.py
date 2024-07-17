from django.contrib import admin
from .models import Engine, Message, Chat

# Register your models here.
admin.site.register(Engine)
admin.site.register(Message)
admin.site.register(Chat)