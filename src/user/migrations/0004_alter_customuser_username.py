# Generated by Django 5.1.1 on 2024-09-16 10:57

import django.core.validators
import user.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0003_alter_customuser_username"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="username",
            field=models.CharField(
                error_messages={
                    "unique": "This username is already taken. Please choose a different one."
                },
                max_length=30,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="username must not start with numeric values nor contains any special chars other than _",
                        regex="^(?!\\d)[^\\@]*$",
                    ),
                    user.validators.no_spaces_validator,
                ],
            ),
        ),
    ]