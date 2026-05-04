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


class SupplierContact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='contacts')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'supplier_contacts'
        ordering = ['-is_primary', 'last_name', 'first_name']
        verbose_name = 'Contact fournisseur'
        verbose_name_plural = 'Contacts fournisseurs'
        indexes = [
            models.Index(fields=['supplier', 'is_primary'], name='idx_sc_supplier_primary'),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.supplier.name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()