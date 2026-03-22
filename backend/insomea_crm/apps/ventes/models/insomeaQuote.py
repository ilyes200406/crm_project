import uuid
from django.db import models
from .opportunity import Opportunity
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from ...users.models.users import User



class InsomeaQuote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opportunity = models.OneToOneField(Opportunity, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='Insomea_quote_created', limit_choices_to={'role': 'COMMERCIAL'}, help_text="Commercial créateur")
    
    reference = models.CharField(max_length=50, unique=True, db_index=True, help_text="Référence unique InsomeaQuote (ex: INSOMEA-2024-00001)")
    document = models.FileField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    subtotal_purchase = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))], help_text="Sous-total achat")
    total_purchase = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))], help_text="Total achat")

    subtotal_sale = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))], help_text="Sous-total vente")
    total_sale = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))], help_text="Total vente")    
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))], help_text="Montant remise")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))], help_text="Remise globale en %")
    margin = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Marge totale")
    margin_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Marge %")

    def calculate_totals(self):
        from django.db.models import Sum

        aggregates = self.lines.aggregate(total_sale=Sum('line_total_sale'))
        self.subtotal_sale = aggregates['total_sale'] or Decimal('0.00')
        
        if self.discount_percent > 0:
            self.discount_amount = (
                self.subtotal_sale * self.discount_percent / Decimal('100.00')
            ).quantize(Decimal('0.01'))
        else:
            self.discount_amount = Decimal('0.00')
        
        self.margin = (self.total_sale - self.total_purchase).quantize(Decimal('0.01'))
        
        if self.total_purchase > 0:
            self.margin_percent = (
                (self.margin / self.total_purchase) * Decimal('100.00')
            ).quantize(Decimal('0.01'))
        else:
            self.margin_percent = Decimal('0.00')
        
        self.save(update_fields=[
            'subtotal_sale',
            'total_sale',
            'discount_amount',
            'margin',
            'margin_percent'
        ])