# Generated by Django 4.2.13 on 2024-07-31 16:17

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("share", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accessrequest",
            name="approval_uuid",
            field=models.UUIDField(
                default=uuid.UUID("bbd04c1d-3a8d-4cde-b0c2-8f2a1249a50e"),
                editable=False,
                unique=True,
            ),
        ),
    ]