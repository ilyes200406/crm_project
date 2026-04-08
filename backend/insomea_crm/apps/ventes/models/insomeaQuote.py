import uuid
from django.db import models
from .opportunity import Opportunity
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from ...users.models.users import User
from datetime import datetime

class InsomeaQuote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opportunity = models.OneToOneField(Opportunity, on_delete=models.CASCADE, related_name='insomea_quote')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='Insomea_quote_created', limit_choices_to={'role': 'COMMERCIAL'}, help_text="Commercial créateur")
    
    reference = models.CharField(max_length=50, unique=True, db_index=True, help_text="Référence unique InsomeaQuote (ex: INSOMEA-2024-00001)")
    document = models.FileField(upload_to='quotes/client/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    subtotal_purchase = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))], help_text="Sous-total achat")
    total_purchase = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))], help_text="Total achat")

    subtotal_sale = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))], help_text="Sous-total vente")
    total_sale = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))], help_text="Total vente")    
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))], help_text="Montant remise")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))], help_text="Remise globale en %")
    margin = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Marge totale")
    margin_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Marge %")


    class Meta:
        indexes = [
            models.Index(fields=['opportunity', 'created_at']),
            models.Index(fields=['reference']),
        ]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        super().save(*args, **kwargs)

    def _generate_reference(self):
        current_year = datetime.now().year
        last_insomea_quote = InsomeaQuote.objects.filter(reference__startswith=f'INSOMEA-{current_year}').order_by('-reference').first()
        if last_insomea_quote:
            last_num = int(last_insomea_quote.reference.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f'INSOMEA-{current_year}-{new_num:05d}'

    def calculate_totals(self):
        from django.db.models import Sum

        aggregates = self.lines.aggregate(
            subtotal_purchase=Sum('line_total_purchase'),
            subtotal_sale=Sum('line_total_sale')
        )
        self.subtotal_purchase = aggregates['subtotal_purchase'] or Decimal('0.00')
        self.subtotal_sale = aggregates['subtotal_sale'] or Decimal('0.00')
        self.total_purchase = self.subtotal_purchase
        
        if self.discount_percent > 0:
            self.discount_amount = (
                self.subtotal_sale * self.discount_percent / Decimal('100.00')
            ).quantize(Decimal('0.01'))
        else:
            self.discount_amount = Decimal('0.00')

        self.total_sale = (self.subtotal_sale - self.discount_amount).quantize(Decimal('0.01'))

        self.margin = (self.total_sale - self.total_purchase).quantize(Decimal('0.01'))
        
        if self.total_purchase > 0:
            self.margin_percent = (
                (self.margin / self.total_purchase) * Decimal('100.00')
            ).quantize(Decimal('0.01'))
        else:
            self.margin_percent = Decimal('0.00')
        
        self.save(update_fields=[
            'subtotal_purchase',
            'total_purchase',
            'subtotal_sale',
            'total_sale',
            'discount_amount',
            'margin',
            'margin_percent'
        ])
