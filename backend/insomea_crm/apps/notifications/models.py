"""
from django.db import models
import uuid

class TypeNotification(models.TextChoices):
    EXPIR_90J = 'EXPIR_90J', 'Expiration 90 jours'
    EXPIR_60J = 'EXPIR_60J', 'Expiration 60 jours'
    EXPIR_30J = 'EXPIR_30J', 'Expiration 30 jours'
    EXPIR_7J = 'EXPIR_7J', 'Expiration 7 jours'
    EXPIR_3J = 'EXPIR_3J', 'Expiration 3 jours'
    NOUVEAU_DEPLOIEMENT = 'NOUVEAU_DEPLOIEMENT', 'Nouveau déploiement'
    DEPLOIEMENT_CONFIRME = 'DEPLOIEMENT_CONFIRME', 'Déploiement confirmé'

class CanalNotif(models.TextChoices):
    EMAIL = 'EMAIL', 'Email'
    IN_APP = 'IN_APP', 'In-app'
    LES_DEUX = 'LES_DEUX', 'Email + In-app'

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opportunity = models.ForeignKey('deploiements.Attribution', on_delete=models.PROTECT, related_name='notifications', null=True, blank=True)
    subscription = models.ForeignKey('authentication.Utilisateur', on_delete=models.PROTECT, related_name='notifications', null=True, blank=True)
    type = models.CharField(max_length=30, choices=TypeNotification.choices)
    titre = models.CharField(max_length=255)
    message = models.TextField()
    canal = models.CharField(max_length=20, choices=CanalNotif.choices, default=CanalNotif.LES_DEUX)
    lu = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-date_envoi']
        indexes = [
            models.Index(fields=['destinataire', 'lu']),
            models.Index(fields=['date_envoi']),
        ]
"""

"""
NOTIFICATION MODEL

Notifications internes (dashboard + email) pour les équipes
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class NotificationType(models.TextChoices):
    """Types notifications"""
    
    # Opportunity workflow
    FINANCE_APPROVE = 'FINANCE_APPROVE', _('Finance: Approuver opportunité')
    
    # Provision workflow
    TECH_PROVISION_WAITING = 'TECH_PROVISION_WAITING', _('Tech: Provision en attente')
    SUBSCRIPTION_PROVISIONED = 'SUBSCRIPTION_PROVISIONED', _('Subscription provisionnée')
    
    # Subscription expiration
    SUBSCRIPTION_EXPIRING = 'SUBSCRIPTION_EXPIRING', _('Subscription expire bientôt')
    SUBSCRIPTION_EXPIRED = 'SUBSCRIPTION_EXPIRED', _('Subscription expirée')


class NotificationStatus(models.TextChoices):
    """Statuts notification"""
    PENDING = 'PENDING', _('En attente')
    SENT = 'SENT', _('Envoyée')
    READ = 'READ', _('Lue')
    FAILED = 'FAILED', _('Échec')


class Notification(models.Model):
    """
    Notification interne
    
    Usage:
        - Affichage dashboard (bell icon)
        - Envoi email optionnel
    """
    
    # ───────────────────────────────────────────────────────
    # IDENTIFICATION
    # ───────────────────────────────────────────────────────
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # ───────────────────────────────────────────────────────
    # TYPE & STATUS
    # ───────────────────────────────────────────────────────
    
    type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        help_text="Type notification"
    )
    
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
        help_text="Statut notification"
    )
    
    # ───────────────────────────────────────────────────────
    # RECIPIENT
    # ───────────────────────────────────────────────────────
    
    recipient = models.ForeignKey(
        'authentication.User',
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Destinataire"
    )
    
    # ───────────────────────────────────────────────────────
    # CONTENT
    # ───────────────────────────────────────────────────────
    
    title = models.CharField(
        max_length=200,
        help_text="Titre notification"
    )
    
    message = models.TextField(
        help_text="Message notification"
    )
    
    # ───────────────────────────────────────────────────────
    # LINKED OBJECTS (optionnel)
    # ───────────────────────────────────────────────────────
    
    opportunity = models.ForeignKey(
        'Opportunity',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="Opportunité liée"
    )
    
    provision = models.ForeignKey(
        'Provision',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="Provision liée"
    )
    
    subscription = models.ForeignKey(
        'Subscription',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="Subscription liée"
    )
    
    # ───────────────────────────────────────────────────────
    # ACTION LINK
    # ───────────────────────────────────────────────────────
    
    action_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="URL action (ex: /opportunities/123/)"
    )
    
    # ───────────────────────────────────────────────────────
    # METADATA
    # ───────────────────────────────────────────────────────
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date/heure envoi"
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date/heure lecture"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # ───────────────────────────────────────────────────────
    # META
    # ───────────────────────────────────────────────────────
    
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
    
    # ───────────────────────────────────────────────────────
    # METHODS
    # ───────────────────────────────────────────────────────
    
    def mark_as_sent(self):
        """Marque notification comme envoyée"""
        from django.utils import timezone
        self.status = NotificationStatus.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_read(self):
        """Marque notification comme lue"""
        from django.utils import timezone
        self.status = NotificationStatus.READ
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at'])
    
    def mark_as_failed(self):
        """Marque notification comme échouée"""
        self.status = NotificationStatus.FAILED
        self.save(update_fields=['status'])