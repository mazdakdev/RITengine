# Generated by Django 5.1.1 on 2024-11-05 20:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventions", "0002_form_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="form",
            name="slug",
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="office",
            name="slug",
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
    ]