from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.

User = get_user_model()

class Office(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    flag = models.ImageField(upload_to='flags/')

    def __str__(self):
        return self.name

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
    office = models.ForeignKey(Office, on_delete=models.CASCADE)
    fields = models.ManyToManyField(Field, related_name='forms')
    image = models.ImageField(upload_to='forms/')
    
    def __str__(self):
        return self.name
    
class Invention(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    values = models.JSONField()

    def __str__(self):
        return f'{self.form} - {self.user}'