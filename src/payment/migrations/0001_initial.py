# Generated by Django 5.1.1 on 2024-09-18 20:37

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Plan",
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
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, null=True)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("interval_count", models.IntegerField(default=1)),
                (
                    "currency",
                    models.CharField(
                        choices=[
                            ("usd", "USD - United States Dollar"),
                            ("eur", "EUR - Euro"),
                            ("gbp", "GBP - British Pound"),
                            ("chf", "CHF - Swiss Franc"),
                            ("aed", "AED - UAE Dirham"),
                        ],
                        max_length=5,
                    ),
                ),
                (
                    "interval",
                    models.CharField(
                        choices=[
                            ("day", "Day"),
                            ("week", "Week"),
                            ("month", "Month"),
                            ("year", "Year"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "stripe_price_id",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Customer",
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
                ("source_id", models.CharField(max_length=255)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="customer",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Subscription",
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
                ("source_id", models.CharField(max_length=255)),
                ("currency", models.CharField(blank=True, max_length=255, null=True)),
                ("amount", models.FloatField(blank=True, null=True)),
                ("status", models.CharField(blank=True, max_length=255, null=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("canceled_at", models.DateTimeField(blank=True, null=True)),
                ("cancel_at_period_end", models.BooleanField(default=False)),
                ("cancel_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscriptions",
                        to="payment.customer",
                    ),
                ),
                (
                    "plan",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="payment.plan",
                    ),
                ),
            ],
        ),
    ]