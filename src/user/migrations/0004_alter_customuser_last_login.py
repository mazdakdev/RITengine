# Generated by Django 4.2.13 on 2024-08-08 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0003_backupcode"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="last_login",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]