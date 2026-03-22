import uuid
from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

from .insomeaQuote import InsomeaQuote
from .opportunityLine import OpportunityLine
from .supplierQuoteLine import SupplierQuoteLine

class InsomeaQuoteLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    insomea_quote = models.ForeignKey(InsomeaQuote, on_delete=models.CASCADE, related_name='lines', help_text="InsomeaQuote parent")
    opportunity_line = models.OneToOneField(OpportunityLine, on_delete=models.CASCADE)
    supplier_quote_line = models.OneToOneField(SupplierQuoteLine, on_delete=models.CASCADE, related_name="insomea_quote_line")

    # snapshot of purchase price (copied from selected SupplierQuoteLine)
    unit_price_purchase = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], help_text="Prix unitaire achat")
    line_total_purchase = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Total achat calculé")
    
    # sale price
    unit_price_sale = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], help_text="Prix unitaire vente")
    line_total_sale = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Total vente calculé")
    line_margin = models.DecimalField(max_digits=12, decimal_places=2)
    line_discount = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):

        self.line_total_sale = (
            Decimal(str(self.opportunity_line.quantity)) * self.unit_price_sale
        ).quantize(Decimal('0.01'))
        
        super().save(*args, **kwargs)
        
        self.insomea_quote.calculate_totals()
    
    
    def get_margin(self):
        return self.line_total_sale - self.line_total_purchase
    
    def get_margin_percent(self):
        if self.line_total_purchase > 0:
            return (
                (self.get_margin() / self.line_total_sale) * Decimal('100.00')
            ).quantize(Decimal('0.01'))
        return Decimal('0.00')