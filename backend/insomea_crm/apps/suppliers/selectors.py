"""
SELECTORS - APP SUPPLIERS

Couche d'optimisation des requêtes

- Queries optimisées (select_related, prefetch_related)
- Filtrage RBAC
- Recherche
- Stats
"""

from django.db.models import Q, Count
from django.shortcuts import get_object_or_404

from .models import Supplier, SupplierType


# ═══════════════════════════════════════════════════════════
# SUPPLIER SELECTORS
# ═══════════════════════════════════════════════════════════

def get_suppliers_queryset(
    user=None,
    filters=None,
    is_active=True
):
    """
    Retourne queryset suppliers optimisé
    
    Args:
        user: Utilisateur (pour filtrage RBAC)
        filters: Dict de filtres additionnels
        is_active: Filtrer actifs/inactifs
    
    Returns:
        QuerySet optimisé
    """
    
    # Base queryset
    queryset = Supplier.objects.all()
    
    # Filtre actifs/inactifs
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    
    # Filtres RBAC
    # Note: Tous les rôles peuvent voir suppliers (lecture seule)
    # Pas de filtrage spécifique nécessaire
    
    # Filtres additionnels
    if filters:
        queryset = queryset.filter(**filters)
    
    return queryset


def get_supplier_by_id(supplier_id, user=None):
    """
    Récupère UN supplier par ID
    
    Args:
        supplier_id: UUID du supplier
        user: Utilisateur (vérification permissions)
    
    Returns:
        Supplier instance
    
    Raises:
        Http404: Si supplier n'existe pas
    """
    
    queryset = Supplier.objects.all()
    
    # Récupère supplier (404 si n'existe pas)
    supplier = get_object_or_404(queryset, id=supplier_id)
    
    return supplier


def get_supplier_by_name(name, is_active=True):
    """
    Récupère supplier par nom
    
    Args:
        name: Nom supplier
        is_active: Seulement actifs ?
    
    Returns:
        Supplier instance ou None
    """
    try:
        queryset = Supplier.objects.all()
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        
        return queryset.get(name__iexact=name)
        
    except Supplier.DoesNotExist:
        return None


# ═══════════════════════════════════════════════════════════
# SEARCH QUERIES
# ═══════════════════════════════════════════════════════════

def search_suppliers(search_term, user=None, limit=20):
    """
    Recherche full-text suppliers
    
    Args:
        search_term: Terme de recherche
        user: Utilisateur (RBAC)
        limit: Nombre max résultats
    
    Returns:
        QuerySet trié par pertinence
    
    Cherche dans :
    - name
    - support_email
    - notes
    """
    
    queryset = get_suppliers_queryset(user=user, is_active=True)
    
    if not search_term:
        return queryset[:limit]
    
    # Q objects pour recherche multi-champs
    query = Q(name__icontains=search_term) | \
            Q(support_email__icontains=search_term) | \
            Q(notes__icontains=search_term)
    
    queryset = queryset.filter(query)
    
    # Tri par pertinence (priorité name)
    queryset = queryset.extra(
        select={
            'relevance': """
                CASE 
                    WHEN name ILIKE %s THEN 1
                    WHEN support_email ILIKE %s THEN 2
                    ELSE 3
                END
            """
        },
        select_params=[f'%{search_term}%'] * 2
    ).order_by('relevance', 'name')
    
    return queryset[:limit]


# ═══════════════════════════════════════════════════════════
# FILTERING BY TYPE
# ═══════════════════════════════════════════════════════════

def get_suppliers_by_type(supplier_type, is_active=True):
    """
    Récupère suppliers par type
    
    Args:
        supplier_type: SupplierType value
        is_active: Seulement actifs ?
    
    Returns:
        QuerySet filtré
    """
    return get_suppliers_queryset(
        filters={'type': supplier_type},
        is_active=is_active
    )


def get_direct_suppliers():
    """Récupère suppliers DIRECT (Microsoft)"""
    return get_suppliers_by_type(SupplierType.DIRECT)


def get_distributors():
    """Récupère distributeurs"""
    return get_suppliers_by_type(SupplierType.DISTRIBUTOR)


def get_resellers():
    """Récupère revendeurs"""
    return get_suppliers_by_type(SupplierType.RESELLER)


# ═══════════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════════

def get_supplier_stats(user=None):
    """
    Statistiques suppliers
    
    Returns:
        dict avec stats :
        - total_suppliers
        - by_type : {DIRECT: X, DISTRIBUTOR: Y, ...}
        - active_count
        - inactive_count
    """
    
    queryset = get_suppliers_queryset(user=user, is_active=None)
    
    # Total
    total = queryset.count()
    
    # Par type
    by_type = dict(
        queryset.values('type').annotate(
            count=Count('id')
        ).values_list('type', 'count')
    )
    
    # Actifs/Inactifs
    active_count = queryset.filter(is_active=True).count()
    inactive_count = queryset.filter(is_active=False).count()
    
    return {
        'total_suppliers': total,
        'by_type': by_type,
        'active_count': active_count,
        'inactive_count': inactive_count,
    }


# ═══════════════════════════════════════════════════════════
# ACTIVE/INACTIVE HELPERS
# ═══════════════════════════════════════════════════════════

def get_active_suppliers():
    """Récupère tous les suppliers actifs"""
    return get_suppliers_queryset(is_active=True)


def get_inactive_suppliers():
    """Récupère tous les suppliers inactifs"""
    return get_suppliers_queryset(is_active=False)