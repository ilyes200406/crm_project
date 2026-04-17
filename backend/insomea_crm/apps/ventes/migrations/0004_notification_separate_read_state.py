"""
Migration: Separate delivery state from read state in Notification model.

- Adds is_read BooleanField (default=False)
- Data migration: rows with status='READ' → is_read=True, status='SENT'
- Removes 'READ' choice from NotificationStatus
"""

from django.db import migrations, models


def migrate_read_status(apps, schema_editor):
    Notification = apps.get_model('ventes', 'Notification')
    Notification.objects.filter(status='READ').update(is_read=True, status='SENT')


def reverse_migrate_read_status(apps, schema_editor):
    Notification = apps.get_model('ventes', 'Notification')
    Notification.objects.filter(is_read=True).update(status='READ')


class Migration(migrations.Migration):

    dependencies = [
        ('ventes', '0003_provision_add_is_renewal_field'),
    ]

    operations = [
        # Step 1: Add is_read field
        migrations.AddField(
            model_name='notification',
            name='is_read',
            field=models.BooleanField(default=False),
        ),

        # Step 2: Data migration — convert existing READ status to is_read=True
        migrations.RunPython(
            migrate_read_status,
            reverse_code=reverse_migrate_read_status,
        ),

        # Step 3: Remove READ from status choices
        migrations.AlterField(
            model_name='notification',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'En attente'),
                    ('SENT', 'Envoyée'),
                    ('FAILED', 'Échec'),
                ],
                default='PENDING',
                max_length=20,
            ),
        ),
    ]
