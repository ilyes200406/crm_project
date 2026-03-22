"""
SUPPLIERS MODELS

Entité unique : Supplier (Fournisseur)

Fournisseurs = Microsoft, Distributeurs, Partenaires
Utilisés dans Opportunities pour sourcing produits
"""

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
    """
    Fournisseur
    
    Relations :
    - Products : Fournit quels produits
    - Opportunities : Utilisé dans opportunités
    
    Champs :
    - Infos entreprise (nom, site web)
    - Contact support (email, téléphone)
    - Type fournisseur
    - Statut actif/inactif
    """
    
    # ───────────────────────────────────────────────────────
    # IDENTIFICATION
    # ───────────────────────────────────────────────────────
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Nom du fournisseur"
    )
    
    type = models.CharField(
        max_length=20,
        choices=SupplierType.choices,
        default=SupplierType.DISTRIBUTOR,
        db_index=True,
        help_text="Type de fournisseur"
    )
    
    # ───────────────────────────────────────────────────────
    # CONTACT INFO
    # ───────────────────────────────────────────────────────
    
    website = models.URLField(
        blank=True,
        validators=[URLValidator()],
        help_text="Site web"
    )
    
    support_email = models.EmailField(
        blank=True,
        help_text="Email support"
    )
    
    support_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Téléphone support"
    )
    
    # ───────────────────────────────────────────────────────
    # ADDITIONAL INFO
    # ───────────────────────────────────────────────────────
    
    notes = models.TextField(
        blank=True,
        help_text="Notes internes"
    )
    
    # ───────────────────────────────────────────────────────
    # STATUS
    # ───────────────────────────────────────────────────────
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Fournisseur actif ?"
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