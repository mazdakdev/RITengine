# Generated by Django 4.2.13 on 2024-08-01 11:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("engine", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EngineCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("prompt", models.TextField()),
            ],
        ),
        migrations.AddField(
            model_name="engine",
            name="category",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="engines",
                to="engine.enginecategory",
            ),
        ),
    ]