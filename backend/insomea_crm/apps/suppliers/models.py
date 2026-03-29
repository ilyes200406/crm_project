import uuid
from django.db import models
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _


class SupplierType(models.TextChoices):
    """
    Types de fournisseurs
    
    DIRECT : Microsoft direct
    DISTRIBUTOR : Distributeur (Ingram, TechData, etc.)
    RESELLER : Revendeur partenaire
    """
    DIRECT = 'DIRECT', _('Direct (Microsoft)')
    DISTRIBUTOR = 'DISTRIBUTOR', _('Distributeur')
    RESELLER = 'RESELLER', _('Revendeur')


class Supplier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255, unique=True, db_index=True)
    type = models.CharField(max_length=20, choices=SupplierType.choices, default=SupplierType.DISTRIBUTOR, db_index=True)
    website = models.URLField(blank=True, validators=[URLValidator()])
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    is_active = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'suppliers'
        ordering = ['name']
        verbose_name = 'Fournisseur'
        verbose_name_plural = 'Fournisseurs'
        
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"