# Generated by Django 4.2.13 on 2024-08-08 20:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0004_alter_customuser_last_login"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="is_phone_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="customuser",
            name="username_change_count",
            field=models.IntegerField(default=0),
        ),
    ]