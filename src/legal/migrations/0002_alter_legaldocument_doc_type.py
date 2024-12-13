# Generated by Django 5.1.1 on 2024-09-17 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("legal", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="legaldocument",
            name="doc_type",
            field=models.CharField(
                choices=[
                    ("privacy_policy", "Privacy Policy"),
                    ("user_guide", "User Guide"),
                    ("terms_of_use", "Terms of Use"),
                    ("share_safety", "Share Safety"),
                    ("license", "License"),
                ],
                max_length=20,
                unique=True,
            ),
        ),
    ]
