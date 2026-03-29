import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class ProductCategory(models.TextChoices):
    OFFICE_365 = 'OFFICE_365', _('Office 365')
    MICROSOFT_365 = 'MICROSOFT_365', _('Microsoft 365')
    WINDOWS = 'WINDOWS', _('Windows')
    AZURE = 'AZURE', _('Azure')
    DYNAMICS = 'DYNAMICS', _('Dynamics 365')
    POWER_PLATFORM = 'POWER_PLATFORM', _('Power Platform')
    SECURITY = 'SECURITY', _('Sécurité')
    OTHER = 'OTHER', _('Autre')


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.PROTECT, related_name='products')
    successor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='predecessors', help_text="Produit remplaçant (si obsolète)")    

    sku = models.CharField(max_length=100, unique=True, db_index=True, help_text="SKU Microsoft (ex: CFQ7TTC0LH18:0001)")
    title = models.CharField(max_length=255, db_index=True, help_text="Nom commercial du produit")
    category = models.CharField(max_length=50, choices=ProductCategory.choices, default=ProductCategory.OTHER, db_index=True)    
    version = models.CharField(max_length=50, blank=True)
    publisher = models.CharField(max_length=255, db_index=True)

    description_technique = models.TextField(blank=True, help_text="Description technique détaillée")
    description_commerciale = models.TextField(blank=True, help_text="Description commerciale pour clients")
    
    is_active = models.BooleanField(default=True, db_index=True, help_text="Produit actif dans le catalogue ?")
    is_deprecated = models.BooleanField(default=False, db_index=True, help_text="Produit obsolète/déprécié ?")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        ordering = ['title', 'version']
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['title']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['supplier', 'is_active']),
        ]
    
    def __str__(self):
        if self.version:
            return f"{self.title} {self.version}"
        return self.title
