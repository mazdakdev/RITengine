# Generated by Django 4.2.13 on 2024-08-08 20:09

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("share", "0013_alter_accessrequest_approval_uuid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accessrequest",
            name="approval_uuid",
            field=models.UUIDField(
                default=uuid.UUID("5f6146a3-d616-4342-b640-e1e016490b13"),
                editable=False,
                unique=True,
            ),
        ),
    ]