from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import uuid
# Create your models here.

User = get_user_model()

class Office(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    flag = models.ImageField(upload_to='flags/')
    slug = models.SlugField(unique=True, editable=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Field(models.Model):
    FIELD_TYPES = [
        ("text", 'Text'),
        ("number", 'Number'),
        ("date", 'Date'),
        ("textarea", 'Textarea'),
    ]
    
    name = models.CharField(max_length=255)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
    is_required = models.BooleanField(default=False)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    options = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name
        
class Form(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    office = models.ForeignKey(
        Office, to_field='slug', on_delete=models.CASCADE, related_name='forms'
    )
    fields = models.ManyToManyField(Field, related_name='forms')
    image = models.ImageField(upload_to='forms/')
    slug = models.SlugField(unique=True, blank=True, null=True, editable=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = str(uuid.uuid4())[:8]
        super(Form, self).save(*args, **kwargs)

    
class Invention(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    values = models.JSONField()

    def __str__(self):
        return f'{self.form} - {self.user}'