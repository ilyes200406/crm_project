import uuid
from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

from .supplierQuote import SupplierQuote
from .opportunityLine import OpportunityLine

class SupplierQuoteLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier_quote = models.ForeignKey(SupplierQuote, related_name="lines", on_delete=models.CASCADE)
    opportunity_line = models.OneToOneField(OpportunityLine, on_delete=models.CASCADE, related_name="supplier_quote_line")

    unit_price_purchase = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], help_text="Prix unitaire achat")
    line_total_purchase = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Total achat calculé")
    currency = models.CharField(max_length=10)
    delivery_time = models.IntegerField(null=True, blank=True)
    sku = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):

        self.line_total_purchase = (
            Decimal(str(self.opportunity_line.quantity)) * self.unit_price_purchase
        ).quantize(Decimal('0.01'))

        super().save(*args, **kwargs)
        self.supplier_quote.calculate_totals()
