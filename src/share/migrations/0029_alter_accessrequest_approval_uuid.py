# Generated by Django 4.2.13 on 2024-08-26 19:34

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("share", "0028_alter_accessrequest_approval_uuid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accessrequest",
            name="approval_uuid",
            field=models.UUIDField(
                default=uuid.UUID("f17e2c6c-b752-4c23-b101-4b9df9b13921"),
                editable=False,
                unique=True,
            ),
        ),
    ]