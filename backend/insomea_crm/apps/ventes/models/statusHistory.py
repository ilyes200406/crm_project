"""
STATUS HISTORY MODEL

Audit trail pour TOUTES les transitions FSM:
- Opportunity transitions
- OpportunityLine transitions
- Provision transitions
- Subscription transitions

Auto-créé via signal post_transition de django-fsm.
Créé manuellement pour les événements non-FSM (création, suppression).
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .opportunity import Opportunity
from .opportunityLine import OpportunityLine
from .provision import Provision
from .subscription import Subscription
from ...users.models.users import User


class StatusHistory(models.Model):

    # ───────────────────────────────────────────────────────
    # IDENTIFICATION
    # ───────────────────────────────────────────────────────

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ───────────────────────────────────────────────────────
    # RELATIONS POLYMORPHIQUES
    # (1 seul sera rempli à la fois)
    # ───────────────────────────────────────────────────────

    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.CASCADE,
        related_name='status_history', null=True, blank=True,
        help_text="Opportunité (si transition Opportunity FSM)"
    )
    opportunity_line = models.ForeignKey(
        OpportunityLine, on_delete=models.CASCADE,
        related_name='status_history', null=True, blank=True,
        help_text="Ligne (si transition OpportunityLine FSM)"
    )
    provision = models.ForeignKey(
        Provision, on_delete=models.CASCADE,
        related_name='status_history', null=True, blank=True,
        help_text="Provision (si transition Provision FSM)"
    )
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE,
        related_name='status_history', null=True, blank=True,
        help_text="Subscription (si transition Subscription FSM)"
    )

    # ───────────────────────────────────────────────────────
    # STATUS CHANGE
    # ───────────────────────────────────────────────────────

    status_precedent = models.CharField(max_length=50, blank=True, help_text="Statut AVANT transition")
    status_suivant = models.CharField(max_length=50, help_text="Statut APRÈS transition")
    transition_name = models.CharField(max_length=100, blank=True, help_text="Nom de la transition FSM")

    # ───────────────────────────────────────────────────────
    # METADATA
    # ───────────────────────────────────────────────────────

    changed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='status_changes',
        help_text="Utilisateur ayant effectué le changement"
    )
    description = models.TextField(blank=True, help_text="Description détaillée du changement")
    metadata = models.JSONField(default=dict, blank=True, help_text="Données additionnelles (JSON)")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="Adresse IP de l'utilisateur")

    # ───────────────────────────────────────────────────────
    # TIMESTAMP
    # ───────────────────────────────────────────────────────

    created_at = models.DateTimeField(auto_now_add=True, db_index=True, help_text="Date/heure du changement")

    # ───────────────────────────────────────────────────────
    # META
    # ───────────────────────────────────────────────────────

    class Meta:
        db_table = 'status_history'
        ordering = ['-created_at']
        verbose_name = 'Historique statut'
        verbose_name_plural = 'Historiques statuts'

        indexes = [
            models.Index(fields=['opportunity', '-created_at']),
            models.Index(fields=['opportunity_line', '-created_at']),
            models.Index(fields=['provision', '-created_at']),
            models.Index(fields=['subscription', '-created_at']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(opportunity__isnull=False, opportunity_line__isnull=True, provision__isnull=True, subscription__isnull=True) |
                    Q(opportunity__isnull=True, opportunity_line__isnull=False, provision__isnull=True, subscription__isnull=True) |
                    Q(opportunity__isnull=True, opportunity_line__isnull=True, provision__isnull=False, subscription__isnull=True) |
                    Q(opportunity__isnull=True, opportunity_line__isnull=True, provision__isnull=True, subscription__isnull=False)
                ),
                name='status_history_only_one_entity_set'
            )
        ]

    def __str__(self):
        entity = self.get_entity_type()
        return f"[{entity}] {self.status_precedent} → {self.status_suivant} ({self.transition_name})"

    # ───────────────────────────────────────────────────────
    # HELPERS
    # ───────────────────────────────────────────────────────

    def get_entity(self):
        if self.opportunity_line_id:
            return self.opportunity_line
        if self.opportunity_id:
            return self.opportunity
        if self.provision_id:
            return self.provision
        if self.subscription_id:
            return self.subscription
        return None

    def get_entity_type(self):
        if self.opportunity_line_id:
            return 'OpportunityLine'
        if self.opportunity_id:
            return 'Opportunity'
        if self.provision_id:
            return 'Provision'
        if self.subscription_id:
            return 'Subscription'
        return None
