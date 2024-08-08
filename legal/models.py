from django.db import models

class LegalDocument(models.Model):
    DOC_TYPES = [
        ('privacy_policy', 'Privacy Policy'),
        ('user_guide', 'User Guide'),
        ('terms_of_use', 'Terms of Use'),
        ('faq', "Ferequently Asked Questions"),
        ('license', "License"),
    ]

    doc_type = models.CharField(max_length=20, choices=DOC_TYPES, unique=True)
    content = models.TextField()
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_doc_type_display()
