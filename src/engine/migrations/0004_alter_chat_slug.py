# Generated by Django 4.2.13 on 2024-08-04 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("engine", "0003_enginecategory_engine_category"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chat",
            name="slug",
            field=models.SlugField(editable=False, max_length=100, unique=True),
        ),
    ]