"""SERVICES - APP PRODUCTS"""

from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from .models import Product
from .validators import validate_product_data, normalize_sku
from .selectors import get_product_by_id


@transaction.atomic
def create_product(*, data: dict, user):
    """Crée un produit"""
    
    # Validation
    validate_product_data(data)
    
    # Normalisation SKU
    if 'sku' in data:
        data['sku'] = normalize_sku(data['sku'])
    
    # Création
    product = Product.objects.create(**data)
    
    return product


@transaction.atomic
def update_product(*, product_id, data: dict, user):
    """Met à jour un produit"""
    
    product = get_product_by_id(product_id, user=user)
    
    # Validation
    validate_product_data(data, product=product)
    
    # Normalisation SKU
    if 'sku' in data:
        data['sku'] = normalize_sku(data['sku'])
    
    # Update
    for field, value in data.items():
        setattr(product, field, value)
    
    product.save()
    
    return product


@transaction.atomic
def deprecate_product(*, product_id, successor_id=None, user=None):
    """Marque un produit comme obsolète"""
    
    product = get_product_by_id(product_id, user=user)
    
    product.is_deprecated = True
    
    if successor_id:
        product.successor_id = successor_id
    
    product.save()
    
    return product