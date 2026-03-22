"""
PRODUCTS MODELS

Catalogue produits Microsoft
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class ProductCategory(models.TextChoices):
    """Catégories produits Microsoft"""
    OFFICE_365 = 'OFFICE_365', _('Office 365')
    MICROSOFT_365 = 'MICROSOFT_365', _('Microsoft 365')
    WINDOWS = 'WINDOWS', _('Windows')
    AZURE = 'AZURE', _('Azure')
    DYNAMICS = 'DYNAMICS', _('Dynamics 365')
    POWER_PLATFORM = 'POWER_PLATFORM', _('Power Platform')
    SECURITY = 'SECURITY', _('Sécurité')
    OTHER = 'OTHER', _('Autre')


class Product(models.Model):
    """
    Produit du catalogue
    
    Exemples :
    - Microsoft 365 Business Standard
    - Office 365 E3
    - Windows 11 Pro
    - Azure AD Premium P1
    """
    
    # ───────────────────────────────────────────────────────
    # IDENTIFICATION
    # ───────────────────────────────────────────────────────
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    sku = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="SKU Microsoft (ex: CFQ7TTC0LH18:0001)"
    )
    
    title = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Nom commercial du produit"
    )
    
    version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Version du produit"
    )
    
    category = models.CharField(
        max_length=50,
        choices=ProductCategory.choices,
        default=ProductCategory.OTHER,
        db_index=True,
        help_text="Catégorie produit"
    )
    
    publisher = models.CharField(max_length=255, db_index=True)
    # ───────────────────────────────────────────────────────
    # DESCRIPTIONS
    # ───────────────────────────────────────────────────────
    
    description_technique = models.TextField(
        blank=True,
        help_text="Description technique détaillée"
    )
    
    description_commerciale = models.TextField(
        blank=True,
        help_text="Description commerciale pour clients"
    )
    
    # ───────────────────────────────────────────────────────
    # RELATIONS
    # ───────────────────────────────────────────────────────
    
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.PROTECT,
        related_name='products',
        help_text="Fournisseur principal"
    )
    
    successor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='predecessors',
        help_text="Produit remplaçant (si obsolète)"
    )
    
    # ───────────────────────────────────────────────────────
    # STATUS
    # ───────────────────────────────────────────────────────
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Produit actif dans le catalogue ?"
    )
    
    is_deprecated = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Produit obsolète/déprécié ?"
    )
    
    # ───────────────────────────────────────────────────────
    # TIMESTAMPS
    # ───────────────────────────────────────────────────────
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ───────────────────────────────────────────────────────
    # META
    # ───────────────────────────────────────────────────────
    
    class Meta:
        db_table = 'products'
        ordering = ['name', 'version']
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['supplier', 'is_active']),
        ]
    
    def __str__(self):
        if self.version:
            return f"{self.name} {self.version}"
        return self.name