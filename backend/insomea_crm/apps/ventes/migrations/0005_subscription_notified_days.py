"""
Migration: Add notified_days ArrayField to Subscription model.

Tracks which expiration thresholds (in days) have already triggered
notifications for a subscription, enabling idempotent Celery task runs.
"""

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('ventes', '0004_notification_separate_read_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='notified_days',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.IntegerField(),
                blank=True,
                default=list,
                help_text="Seuils (en jours) pour lesquels une notification d'expiration a déjà été envoyée (ex: [90, 30, 7])",
                size=None,
            ),
        ),
    ]
