import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from django.utils import timezone

from ...users.models.users import User
from .opportunityLine import OpportunityLine
from .subscription import Subscription


class ProvisionStatus(models.TextChoices):
    WAITING_PROVISION = 'WAITING_PROVISION', _('À approvisionner')
    PROVISIONING = 'PROVISIONING', _('En cours approvisionnement')
    PROVISIONED = 'PROVISIONED', _('Terminé')
    ERROR = 'ERROR', _('erreur')

class Provision(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opportunity_line = models.OneToOneField(OpportunityLine, on_delete=models.PROTECT, related_name="provision")
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True, blank=True, related_name="provisions")
    subscription_term = models.ForeignKey('SubscriptionTerm', null=True, blank=True, on_delete=models.CASCADE, related_name='provision')
    provisionned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'TECHNICIEN'})
    
    microsoft_subscription_id = models.CharField(max_length=255, blank=True, help_text="Subscription ID Microsoft")
    provisioning_started_at = models.DateTimeField(null=True, blank=True, help_text="Date début provisionnement")
    provisioning_completed_at = models.DateTimeField(null=True, blank=True, help_text="Date fin provisionnement")
    provisioning_error = models.TextField(blank=True, help_text="Erreur provisionnement (si échec)")

    status = FSMField(max_length=50, choices=ProvisionStatus.choices, default=ProvisionStatus.WAITING_PROVISION, protected=True, db_index=True)

    class Meta:
        db_table = 'provisions'
        ordering = ['-created_at']
        verbose_name = 'Provision'
        verbose_name_plural = 'Provisions'
        
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['provisionned_by', 'status']),
            models.Index(fields=['opportunity_line']),
            models.Index(fields=['subscription']),
        ]
    

    @transition(field=status, source=ProvisionStatus.WAITING_PROVISION, target=ProvisionStatus.PROVISIONING)
    def start(self, technician=None):
        self.provisionned_by = technician
        self.provisioning_started_at = timezone.now()
    
    @transition(field=status, source=ProvisionStatus.PROVISIONING, target=ProvisionStatus.PROVISIONED, conditions=[lambda instance: instance.has_subscription()])
    def complete_provisioning(self, subscription_id=None):
        if subscription_id:
            self.microsoft_subscription_id = subscription_id
        self.provisioning_completed_at = timezone.now()
    def has_subscription(self):
        return hasattr(self, 'subscription') and self.subscription is not None
    
    @transition(field=status, source=ProvisionStatus.PROVISIONING, target=ProvisionStatus.ERROR)
    def fail_provisioning(self, error_message):
        self.provisioning_error = error_message

    @transition(field=status, source=ProvisionStatus.ERROR, target=ProvisionStatus.PROVISIONING)
    def restart(self):
        pass

    def has_subscription(self):
        """
        Vérifie si provision a subscription
        
        MODIFIÉ: Check subscription FK au lieu de reverse OneToOne
        
        Returns:
            bool
        """
        return self.subscription is not None
    
    def is_renewal(self):
        return self.subscription is not None
    
    def is_initial(self):
        return self.subscription is None