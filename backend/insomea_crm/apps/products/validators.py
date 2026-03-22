"""VALIDATORS - APP PRODUCTS"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_microsoft_sku(value):
    """
    Valide SKU Microsoft
    
    Format : PRODUCTID:VARIANTID
    Exemple : CFQ7TTC0LH18:0001
    """
    if not value:
        return
    
    pattern = r'^[A-Z0-9]{8,20}:\d{4}$'
    
    if not re.match(pattern, value.upper()):
        raise ValidationError(
            _('SKU Microsoft invalide. Format attendu : PRODUCTID:VARIANTID (ex: CFQ7TTC0LH18:0001)'),
            code='invalid_sku'
        )


def validate_sku_unique(sku, exclude_id=None):
    """Valide unicité SKU"""
    from .models import Product
    
    sku_normalized = sku.strip().upper()
    
    query = Product.objects.filter(sku__iexact=sku_normalized)
    
    if exclude_id:
        query = query.exclude(id=exclude_id)
    
    if query.exists():
        raise ValidationError(
            _('Un produit avec ce SKU existe déjà'),
            code='duplicate_sku'
        )


def validate_product_data(data, product=None):
    """Validation composite"""
    errors = {}
    
    # Valide SKU
    if 'sku' in data:
        try:
            validate_microsoft_sku(data['sku'])
        except ValidationError as e:
            errors['sku'] = e.messages
        
        try:
            exclude_id = product.id if product else None
            validate_sku_unique(data['sku'], exclude_id)
        except ValidationError as e:
            errors['sku'] = e.messages
    
    if errors:
        raise ValidationError(errors)
    
    return data


def normalize_sku(sku):
    """Normalise SKU (uppercase, trim)"""
    if not sku:
        return sku
    return sku.strip().upper()