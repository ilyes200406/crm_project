"""
SERVICES - APP SUPPLIERS

Business Logic Layer

- Création supplier
- Update supplier
- Activation/Désactivation
- Audit logging (optionnel - pas de SupplierHistory pour simplifier)
"""

from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied

from .models import Supplier
from .validators import (
    validate_supplier_data,
    normalize_supplier_name,
    normalize_phone_number,
    normalize_url,
)
from .selectors import get_supplier_by_id


# ═══════════════════════════════════════════════════════════
# SUPPLIER CREATION
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def create_supplier(*, data: dict, user):
    """
    Crée un nouveau fournisseur
    
    Args:
        data: Données supplier validées
        user: Utilisateur créateur
    
    Returns:
        Supplier instance créée
    
    Raises:
        ValidationError: Si données invalides
        PermissionDenied: Si user sans permission
    
    Business Rules :
    - ADMIN ou FINANCE peuvent créer
    - Nom unique (case-insensitive)
    - Normalisation automatique
    """
    
    # ───────────────────────────────────────────────────────
    # 1. VALIDATION DONNÉES
    # ───────────────────────────────────────────────────────
    
    validate_supplier_data(data)
    
    # ───────────────────────────────────────────────────────
    # 3. NORMALISATION
    # ───────────────────────────────────────────────────────
    
    if 'name' in data:
        data['name'] = normalize_supplier_name(data['name'])
    
    if 'support_phone' in data and data['support_phone']:
        data['support_phone'] = normalize_phone_number(data['support_phone'])
    
    if 'website' in data and data['website']:
        data['website'] = normalize_url(data['website'])
    
    # ───────────────────────────────────────────────────────
    # 4. CRÉATION SUPPLIER
    # ───────────────────────────────────────────────────────
    
    supplier = Supplier.objects.create(**data)
    
    return supplier


# ═══════════════════════════════════════════════════════════
# SUPPLIER UPDATE
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def update_supplier(*, supplier_id, data: dict, user):
    """
    Met à jour un fournisseur existant
    
    Args:
        supplier_id: UUID du supplier
        data: Données à mettre à jour (partial)
        user: Utilisateur modifiant
    
    Returns:
        Supplier instance mise à jour
    
    Raises:
        ValidationError: Si données invalides
        PermissionDenied: Si user sans permission
        Http404: Si supplier n'existe pas
    """
    
    # ───────────────────────────────────────────────────────
    # 1. RÉCUPÉRATION SUPPLIER
    # ───────────────────────────────────────────────────────
    
    supplier = get_supplier_by_id(supplier_id, user=user)
    
    # ───────────────────────────────────────────────────────
    # 2. VALIDATION DONNÉES
    # ───────────────────────────────────────────────────────
    
    validate_supplier_data(data, supplier=supplier)
    
    # ───────────────────────────────────────────────────────
    # 4. NORMALISATION
    # ───────────────────────────────────────────────────────
    
    if 'name' in data:
        data['name'] = normalize_supplier_name(data['name'])
    
    if 'support_phone' in data and data['support_phone']:
        data['support_phone'] = normalize_phone_number(data['support_phone'])
    
    if 'website' in data and data['website']:
        data['website'] = normalize_url(data['website'])
    
    # ───────────────────────────────────────────────────────
    # 5. UPDATE SUPPLIER
    # ───────────────────────────────────────────────────────
    
    for field, value in data.items():
        setattr(supplier, field, value)
    
    supplier.save()
    
    return supplier


# ═══════════════════════════════════════════════════════════
# SUPPLIER ACTIVATION/DEACTIVATION
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def activate_supplier(*, supplier_id, user):
    """
    Active un fournisseur
    
    Args:
        supplier_id: UUID supplier
        user: Utilisateur
    
    Returns:
        Supplier activé
    """
    
    supplier = get_supplier_by_id(supplier_id, user=user)
    
    if supplier.is_active:
        raise ValidationError('Ce fournisseur est déjà actif')
    
    supplier.is_active = True
    supplier.save(update_fields=['is_active'])
    
    return supplier


@transaction.atomic
def deactivate_supplier(*, supplier_id, user):
    """
    Désactive un fournisseur
    
    Args:
        supplier_id: UUID supplier
        user: Utilisateur
    
    Returns:
        Supplier désactivé
    
    Business Rules :
    - ADMIN seulement
    - Pas de suppression (soft delete via is_active)
    """
    
    supplier = get_supplier_by_id(supplier_id, user=user)
    
    if not supplier.is_active:
        raise ValidationError('Ce fournisseur est déjà inactif')
    
    supplier.is_active = False
    supplier.save(update_fields=['is_active'])
    
    return supplier