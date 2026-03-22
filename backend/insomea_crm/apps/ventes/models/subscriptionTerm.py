"""
Terme de subscription (période contractuelle)
Exemple:
    Subscription Office 365:
    - Term 1: 2024-01-01 → 2025-01-01 (Opportunity #1 INITIAL)
    - Term 2: 2025-01-01 → 2026-01-01 (Opportunity #2 RENEWAL)
    - Term 3: 2026-01-01 → 2027-01-01 (Opportunity #3 RENEWAL)
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from .subscription import Subscription
from .provision import Provision


class SubscriptionTerm(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE,related_name='terms')
    opportunity = models.ForeignKey('Opportunity', on_delete=models.PROTECT, related_name='subscription_terms', help_text="Opportunité ayant généré ce terme (INITIAL ou RENEWAL)")

    term_number = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    start_date = models.DateField()
    end_date = models.DateField()
    
    # PRICING SNAPSHOT (prix ce terme)
    unit_price_purchase = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    unit_price_sale = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    total_purchase = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    total_sale = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    auto_renew_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscription_terms'
        ordering = ['subscription', 'term_number']
        verbose_name = 'Terme subscription'
        verbose_name_plural = 'Termes subscriptions'
        
        constraints = [
            models.UniqueConstraint(
                fields=['subscription', 'term_number'],
                name='unique_subscription_term_number'
            ),
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F('start_date')),
                name='term_end_after_start'
            ),
        ]
        
        indexes = [
            models.Index(fields=['subscription', 'term_number']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"Term {self.term_number} - {self.subscription.subscription_number} ({self.start_date} → {self.end_date})"
    
    # ───────────────────────────────────────────────────────
    # METHODS
    # ───────────────────────────────────────────────────────
    
    def save(self, *args, **kwargs):
        """
        Calculate totals before save
        """
        # Récupère quantity depuis subscription
        quantity = self.subscription.quantity
        
        # Calcule totaux
        self.total_purchase = self.unit_price_purchase * quantity
        self.total_sale = self.unit_price_sale * quantity
        
        super().save(*args, **kwargs)
    
    @property
    def margin(self):
        """Marge ce terme"""
        return self.total_sale - self.total_purchase
    
    @property
    def margin_percent(self):
        """Marge % ce terme"""
        if self.total_purchase > 0:
            return (self.margin / self.total_purchase) * Decimal('100.00')
        return Decimal('0.00')
    
    @property
    def duration_days(self):
        """Durée terme en jours"""
        return (self.end_date - self.start_date).days
    
    def is_current(self):
        """Vérifie si ce terme est actuel"""
        from datetime import date
        today = date.today()
        return self.start_date <= today <= self.end_date
    
    def is_past(self):
        """Vérifie si ce terme est passé"""
        from datetime import date
        return self.end_date < date.today()
    
    def is_future(self):
        """Vérifie si ce terme est futur"""
        from datetime import date
        return self.start_date > date.today()