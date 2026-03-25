import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from datetime import datetime


from ...users.models.users import User
from ...clients.models import Client

class OpportunityType(models.TextChoices):
    INITIAL = 'INITIAL', _('Vente initiale')
    RENEWAL = 'RENEWAL', _('Renouvellement')
    UPSELL = 'UPSELL', _('Vente additionnelle')
    DOWNGRADE = 'DOWNGRADE', _('Réduction')

class OpportunityStatus(models.TextChoices):
    DRAFT = 'DRAFT', _('Brouillon')
    SUPPLIER_QUOTE_REQUEST = 'SUPPLIER_QUOTE_REQUEST', _('Devis fournisseur demandé')
    SUPPLIER_QUOTE_RECIEVED = 'SUPPLIER_QUOTE_RECIEVED', _('Devis fournisseur reçu')
    INSOMEA_QUOTE_CREATED = 'INSOMEA_QUOTE_CREATED', _('Devis Insomea créé')
    CLIENT_PO_REQUEST = 'CLIENT_PO_REQUEST', _('BC client demandé')
    CLIENT_PO_RECIEVED = 'CLIENT_PO_RECIEVED', _('BC client reçu')
    APPROUVED = 'APPROUVED', _('approuvée')
    CANCELLED = 'CANCELLED', _('Annulé')                    

class Opportunity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='Opportunities', db_index=True, help_text="Client concerné")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='Opportunities_created', limit_choices_to={'role': 'COMMERCIAL'}, help_text="Commercial créateur")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='Opportunities_assigned', limit_choices_to={'role__in': ['COMMERCIAL', 'TECHNICIEN', 'FINANCE']}, db_index=True, help_text="Utilisateur assigné (responsable actuel)")
    related_opportunity = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_opportunities', help_text="Opportunité parente (si renewal/upsell/downgrade)")

    reference = models.CharField(max_length=50, unique=True, db_index=True, help_text="Référence unique Opportunity (ex: OPP-2024-00001)")
    name = models.CharField(max_length=255, help_text="Nom descriptif du Opportunity")
    status = FSMField(max_length=50, choices=OpportunityStatus.choices, default=OpportunityStatus.DRAFT, db_index=True)
    type = models.CharField(max_length=20, choices=OpportunityType.choices, default=OpportunityType.INITIAL, help_text="Type opportunité")
    notes = models.TextField(blank=True, help_text="Notes internes")
    cancellation_reason = models.TextField(blank=True, help_text="Raison annulation")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Opportunities'
        ordering = ['-created_at']
        
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['client', 'status']),
            models.Index(fields=['created_by', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['type', 'created_at']),
            models.Index(fields=['related_opportunity']),
        ]
        
        verbose_name = 'Opportunity'
        verbose_name_plural = 'Opportunities'
    
    def __str__(self):
        return f"{self.reference} - {self.client.company_name}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        super().save(*args, **kwargs)
    
    def _generate_reference(self):
        current_year = datetime.now().year
        last_Opportunity = Opportunity.objects.filter(reference__startswith=f'OPP-{current_year}').order_by('-reference').first()
        if last_Opportunity:
            last_num = int(last_Opportunity.reference.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f'OPP-{current_year}-{new_num:05d}'
    
    def can_edit(self):
        editable_statuses = [
            OpportunityStatus.DRAFT,
            OpportunityStatus.SUPPLIER_QUOTE_REQUEST,
            OpportunityStatus.SUPPLIER_QUOTE_RECIEVED,
            OpportunityStatus.INSOMEA_QUOTE_CREATED,
            OpportunityStatus.CLIENT_PO_REQUEST,
        ]
        return self.status in editable_statuses
    
    def can_add_items(self):
        return self.can_edit()
    
    def is_renewal(self):
        return self.type == OpportunityType.RENEWAL
    
    def is_initial(self):
        return self.type == OpportunityType.INITIAL
    
    def get_parent_opportunity(self):
        return self.related_opportunity
    
    def get_child_opportunities(self):
        return self.child_opportunities.all()

    
    # HELPERS
    
    def all_lines_have_status(self, target_status):
        return self.lines.count() > 0 and all(l.status == target_status for l in self.lines.all())

    # LINE-DRIVEN TRANSITIONS

    @transition(field=status, source=OpportunityStatus.DRAFT, target=OpportunityStatus.SUPPLIER_QUOTE_REQUEST)
    def all_supplier_quotes_requested(self):
        pass

    @transition(field=status, source=OpportunityStatus.SUPPLIER_QUOTE_REQUEST, target=OpportunityStatus.SUPPLIER_QUOTE_RECIEVED)
    def all_supplier_quotes_received(self):
        pass


    # NORMAL BUSINESS TRANSITIONS

    @transition(field=status, source=OpportunityStatus.SUPPLIER_QUOTE_RECIEVED, target=OpportunityStatus.INSOMEA_QUOTE_CREATED, conditions=[lambda instance: instance.has_insomea_quote()])
    def create_insomea_quote(self):
        pass
    def has_insomea_quote(self):
        try:
            return self.insomea_quote is not None
        except self.__class__.insomea_quote.RelatedObjectDoesNotExist:
            return False
    
    @transition(field=status, source=OpportunityStatus.INSOMEA_QUOTE_CREATED, target=OpportunityStatus.CLIENT_PO_REQUEST)
    def request_client_po(self):
        pass

    @transition(field=status, source=OpportunityStatus.CLIENT_PO_REQUEST, target=OpportunityStatus.CLIENT_PO_RECIEVED, conditions=[lambda instance: instance.opportunity_has_client_po()])
    def receive_client_po(self):
        pass
    def opportunity_has_client_po(self):
        try:
            return self.client_purchase_order is not None
        except self.__class__.client_purchase_order.RelatedObjectDoesNotExist:
            return False
    
    @transition(field=status, source=OpportunityStatus.CLIENT_PO_RECIEVED, target=OpportunityStatus.APPROUVED)
    def approuve(self):
        pass

    @transition(
        field=status,
        source=[
            OpportunityStatus.DRAFT,
            OpportunityStatus.SUPPLIER_QUOTE_REQUEST,
            OpportunityStatus.SUPPLIER_QUOTE_RECIEVED,
            OpportunityStatus.INSOMEA_QUOTE_CREATED,
            OpportunityStatus.CLIENT_PO_REQUEST,
        ],
        target=OpportunityStatus.CANCELLED
    )
    def cancel(self, reason=''):
        if reason:
            self.notes = f"ANNULÉ : {reason}\n\n{self.notes}"
