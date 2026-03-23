import uuid
from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime

from ...users.models.users import User
from ...suppliers.models import Supplier


class SupplierQuote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='Supplier_quote_created', limit_choices_to={'role': 'COMMERCIAL'}, help_text="Commercial créateur")    
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)

    reference = models.CharField(max_length=50, unique=True, db_index=True, help_text="Référence unique SupplierQuote")
    document = models.FileField()
    recieved_at = models.DateTimeField(auto_now_add=True, db_index=True)

    subtotal_purchase = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))], help_text="Sous-total achat")
    total_purchase = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))], help_text="Total achat")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))], help_text="Montant remise")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))], help_text="Remise globale en %")

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        super().save(*args, **kwargs)

    def _generate_reference(self):
        current_year = datetime.now().year
        last_quote = SupplierQuote.objects.filter(
            reference__startswith=f'SUP-{current_year}'
        ).order_by('-reference').first()

        if last_quote:
            last_num = int(last_quote.reference.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f'SUP-{current_year}-{new_num:05d}'

    @property
    def received_at(self):
        return self.recieved_at

    @property
    def created_at(self):
        return self.recieved_at

    def calculate_totals(self):
        from django.db.models import Sum
        
        aggregates = self.lines.aggregate(subtotal_purchase=Sum('line_total_purchase'))
        self.subtotal_purchase = aggregates['subtotal_purchase'] or Decimal('0.00')
        
        if self.discount_percent > 0:
            self.discount_amount = (
                self.subtotal_purchase * self.discount_percent / Decimal('100.00')
            ).quantize(Decimal('0.01'))
        else:
            self.discount_amount = Decimal('0.00')
        
        self.total_purchase = (self.subtotal_purchase - self.discount_amount).quantize(Decimal('0.01'))
        
        self.save(update_fields=[
            'subtotal_purchase',
            'discount_amount', 
            'total_purchase'
        ])
