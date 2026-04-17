"""
NOTIFICATION MODEL

Notifications internes (dashboard + email) pour les équipes
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class NotificationType(models.TextChoices):
    # Opportunity workflow
    FINANCE_APPROVE = 'FINANCE_APPROVE', _('Finance: Approuver opportunité')
    
    # Provision workflow
    TECH_PROVISION_WAITING = 'TECH_PROVISION_WAITING', _('Tech: Provision en attente')
    SUBSCRIPTION_PROVISIONED = 'SUBSCRIPTION_PROVISIONED', _('Subscription provisionnée')
    
    # Subscription expiration
    SUBSCRIPTION_EXPIRING = 'SUBSCRIPTION_EXPIRING', _('Subscription expire bientôt')
    SUBSCRIPTION_EXPIRED = 'SUBSCRIPTION_EXPIRED', _('Subscription expirée')


class NotificationStatus(models.TextChoices):
    PENDING = 'PENDING', _('En attente')
    SENT = 'SENT', _('Envoyée')
    FAILED = 'FAILED', _('Échec')


class Notification(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opportunity = models.ForeignKey('Opportunity', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    provision = models.ForeignKey('Provision', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    subscription = models.ForeignKey('Subscription', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')

    recipient = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='notifications', help_text="Destinataire")
    type = models.CharField(max_length=50, choices=NotificationType.choices, help_text="Type notification")
    title = models.CharField(max_length=200)
    message = models.TextField()
    action_url = models.CharField(max_length=500, blank=True, help_text="URL action (ex: /opportunities/123/)")
    status = models.CharField(max_length=20, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    is_read = models.BooleanField(default=False)

    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        
        indexes = [
            models.Index(fields=['recipient', 'status', '-created_at']),
            models.Index(fields=['type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} → {self.recipient.get_full_name()}"
    
    def mark_as_sent(self):
        """Marque notification comme envoyée"""
        from django.utils import timezone
        self.status = NotificationStatus.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_read(self):
        """Marque notification comme lue"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_failed(self):
        """Marque notification comme échouée"""
        self.status = NotificationStatus.FAILED
        self.save(update_fields=['status'])
