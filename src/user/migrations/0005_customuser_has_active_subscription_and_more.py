# Generated by Django 5.1.1 on 2024-09-17 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0004_alter_customuser_username"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="has_active_subscription",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="customuser",
            name="stripeCustomerId",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="customuser",
            name="stripeSubscriptionId",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="customuser",
            name="trial_start_date",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]