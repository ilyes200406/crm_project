import uuid

from django.db import models

from ...users.models.users import User
from ...suppliers.models import Supplier


class InsomeaPurchaseOrder(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='insomea_pos',
        help_text="Fournisseur destinataire du BC"
    )
    supplier_quote = models.ForeignKey(
        'SupplierQuote',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='insomea_pos',
        help_text="Devis fournisseur sur lequel ce BC est basé"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insomea_pos_created',
        limit_choices_to={'role_id': 'FINANCE'},
        help_text="Finance créateur"
    )

    po_number = models.CharField(max_length=100, unique=True, db_index=True)
    document = models.FileField(upload_to='po/insomea/', null=True, blank=True)

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date d'envoi au fournisseur"
    )
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date de confirmation par le fournisseur"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    @property
    def total_purchase(self):
        return self.supplier_quote.total_purchase
    
    @property
    def lines_count(self):
        return self.supplier_quote.lines.count()
    
    @property
    def opportunity_lines(self):
        return [
            sq_line.opportunity_line
            for sq_line in self.supplier_quote.lines.all()
        ]
        
    class Meta:
        db_table = 'insomea_purchase_orders'
        ordering = ['-created_at']
        verbose_name = 'BC Insomea'
        verbose_name_plural = 'BCs Insomea'

    def __str__(self):
        return f"{self.po_number} → {self.supplier.name}"

    def is_sent(self):
        return self.sent_at is not None

    def is_confirmed(self):
        return self.confirmed_at is not None