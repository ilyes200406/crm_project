import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from decimal import Decimal
from django.utils import timezone

from .opportunity import Opportunity
from ...products.models import Product
from .insomeaPurchaseOrder import InsomeaPurchaseOrder
from ...users.models.users import User

class OpportunityLineStatus(models.TextChoices):
    DRAFT = 'DRAFT', _('Brouillon')
    SUPPLIER_QUOTE_REQUEST = 'SUPPLIER_QUOTE_REQUEST', _('Devis fournisseur demandé')
    SUPPLIER_QUOTE_RECIEVED = 'SUPPLIER_QUOTE_RECIEVED', _('Devis fournisseur reçu')
    CANCELLED = 'CANCELLED', _('Annulé')

class BillingCycle(models.TextChoices):
    MONTHLY = 'MONTHLY', _('Mensuel')
    ANNUAL = 'ANNUAL', _('Annuel')

class OpportunityLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='lines', help_text="Opportunity parent")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    insomea_purchase_order = models.ForeignKey(InsomeaPurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='Insomea_purchase_order')
    renewal_of_subscription = models.ForeignKey('Subscription', on_delete=models.SET_NULL, null=True, blank=True, related_name='renewal_lines', help_text="Subscription renouvelée (si Opportunity.type=RENEWAL)")

    billing_cycle = models.CharField(max_length=20, choices=BillingCycle.choices, default=BillingCycle.ANNUAL, help_text="Cycle de facturation")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], help_text="Quantité de licences")
    notes = models.TextField(blank=True, help_text="Notes spécifiques ligne")
    status = FSMField(max_length=50, choices=OpportunityLineStatus.choices, default=OpportunityLineStatus.DRAFT, protected=True, db_index=True, help_text="Statut FSM de la ligne")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'Opportunity_Lines'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['opportunity', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['opportunity', 'product'],
                name='unique_product_per_Opportunity'
            )
        ]
        verbose_name = 'Opportunity line'
        verbose_name_plural = 'Opportunity lines'
    
    def __str__(self):
        return f"{self.product.title} x{self.quantity} - {self.opportunity.reference}"

    @transition(field=status, source=OpportunityLineStatus.DRAFT, target=OpportunityLineStatus.SUPPLIER_QUOTE_REQUEST)
    def request_supplier_quote(self):
        pass
    
    @transition(field=status, source=OpportunityLineStatus.SUPPLIER_QUOTE_REQUEST, target=OpportunityLineStatus.SUPPLIER_QUOTE_RECIEVED, conditions=[lambda instance: instance.has_supplier_quote()])
    def supplier_quote_received(self):
        pass
    def has_supplier_quote(self):
        return self.supplier_quote_lines.exists()
    
    @transition(field=status, source="*", target=OpportunityLineStatus.CANCELLED)
    def cancel(self, reason=''):
        if reason:
            self.notes = f"ANNULÉ : {reason}\n\n{self.notes}"









    def is_renewal(self):
        return self.renewal_of_subscription is not None
    
    def get_original_subscription(self):
        return self.renewal_of_subscription