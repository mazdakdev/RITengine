# Generated by Django 5.1.1 on 2024-11-04 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="form",
            name="fields",
            field=models.ManyToManyField(related_name="forms", to="inventions.field"),
        ),
    ]