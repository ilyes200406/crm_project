import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from django.core.validators import MinValueValidator

class SubscriptionStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', _('Active')
    PENDING_RENEWAL = 'PENDING_RENEWAL', _('En attente renouvellement')
    EXPIRED = 'EXPIRED', _('Expirée')
    CANCELLED = 'CANCELLED', _('Annulée')

class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey('clients.Client', on_delete=models.PROTECT, related_name='subscriptions', help_text="Client propriétaire")
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='subscriptions')

    subscription_number = models.CharField(max_length=100)
    current_term_start = models.DateField()
    current_term_end = models.DateField()
    
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantité licences"
    )
    
    billing_cycle = models.CharField(
        max_length=20,
        choices=[
            ('MONTHLY', 'Mensuel'),
            ('ANNUAL', 'Annuel'),
        ],
        help_text="Cycle de facturation"
    )

    auto_renew = models.BooleanField(
        default=True,
        help_text="Renouvellement automatique activé"
    )

    status = FSMField(choices=SubscriptionStatus.choices, default=SubscriptionStatus.ACTIVE, protected=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        
        indexes = [
            models.Index(fields=['subscription_number']),
            models.Index(fields=['client', 'status']),
            models.Index(fields=['product', 'status']),
            models.Index(fields=['current_term_end', 'status']),
        ]
    
    def __str__(self):
        return f"{self.subscription_number} - {self.product.title} ({self.client.company_name})"
    

    @transition(field=status, source=SubscriptionStatus.ACTIVE, target=SubscriptionStatus.PENDING_RENEWAL)
    def mark_pending_renewal(self):
        # Called by: Celery task (30j avant expiration)
        pass
    
    @transition(field=status, source=[SubscriptionStatus.PENDING_RENEWAL, SubscriptionStatus.EXPIRED], target=SubscriptionStatus.ACTIVE)
    def renew(self, new_term):
        # Called by: provision_service.complete_provisioning() (renewal)
        self.current_term_start = new_term.start_date
        self.current_term_end = new_term.end_date
    
    @transition(field=status, source=SubscriptionStatus.PENDING_RENEWAL, target=SubscriptionStatus.EXPIRED)
    def expire(self):
        # Called by: Celery task (si end_date < today et pas renouvelée)
        pass
    
    @transition(field=status, source=SubscriptionStatus.EXPIRED, target=SubscriptionStatus.CANCELLED)
    def cancel(self, reason=''):
        # Called by: subscription_service.cancel_subscription()
        pass
    
    def get_current_term(self):
        from datetime import date
        today = date.today()
        
        return self.terms.filter(start_date__lte=today, end_date__gte=today).first()
    
    def get_all_terms(self):
        return self.terms.all().order_by('term_number')
    
    def get_latest_term(self):
        return self.terms.order_by('-term_number').first()
    
    def is_expiring_soon(self, days=30):
        if not self.current_term_end:
            return False
        
        from datetime import date, timedelta
        threshold = date.today() + timedelta(days=days)
        
        return self.current_term_end <= threshold
    
    def days_until_expiration(self):
        if not self.current_term_end:
            return None
        
        from datetime import date
        delta = self.current_term_end - date.today()
        return delta.days if delta.days > 0 else 0
    
    @property
    def is_active(self):
        return self.status == SubscriptionStatus.ACTIVE