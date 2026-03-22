"""SELECTORS - APP PRODUCTS"""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Product


def get_products_queryset(user=None, filters=None, is_active=True):
    """Retourne queryset products optimisé"""
    queryset = Product.objects.select_related('supplier', 'successor')
    
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    
    if filters:
        queryset = queryset.filter(**filters)
    
    return queryset


def get_product_by_id(product_id, user=None):
    """Récupère product par ID"""
    return get_object_or_404(
        Product.objects.select_related('supplier', 'successor'),
        id=product_id
    )


def get_product_by_sku(sku):
    """Récupère product par SKU"""
    try:
        return Product.objects.select_related('supplier').get(sku__iexact=sku)
    except Product.DoesNotExist:
        return None


def search_products(search_term, user=None, limit=20):
    """Recherche full-text products"""
    queryset = get_products_queryset(user=user, is_active=True)
    
    if not search_term:
        return queryset[:limit]
    
    query = Q(sku__icontains=search_term) | \
            Q(name__icontains=search_term) | \
            Q(description_commerciale__icontains=search_term)
    
    return queryset.filter(query)[:limit]


def get_products_by_category(category, is_active=True):
    """Récupère products par catégorie"""
    return get_products_queryset(
        filters={'category': category},
        is_active=is_active
    )


def get_products_by_supplier(supplier_id, is_active=True):
    """Récupère products d'un fournisseur"""
    return get_products_queryset(
        filters={'supplier_id': supplier_id},
        is_active=is_active
    )