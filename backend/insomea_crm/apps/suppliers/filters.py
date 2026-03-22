"""
FILTERS - APP SUPPLIERS

Filtrage et recherche avancés

- Filtre par type (DIRECT, DISTRIBUTOR, RESELLER)
- Filtre actif/inactif
- Recherche full-text (nom, email)
- Tri dynamique
"""

import django_filters
from django.db.models import Q

from .models import Supplier, SupplierType


# ═══════════════════════════════════════════════════════════
# SUPPLIER FILTER
# ═══════════════════════════════════════════════════════════

class SupplierFilter(django_filters.FilterSet):
    """
    Filtres pour modèle Supplier
    
    Usage :
    GET /api/suppliers/?type=DIRECT
    GET /api/suppliers/?is_active=true
    GET /api/suppliers/?search=Microsoft
    GET /api/suppliers/?name=microsoft
    """
    
    # ───────────────────────────────────────────────────────
    # EXACT FILTERS
    # ───────────────────────────────────────────────────────
    
    type = django_filters.ChoiceFilter(
        field_name='type',
        choices=SupplierType.choices,
        label='Type de fournisseur'
    )
    
    is_active = django_filters.BooleanFilter(
        field_name='is_active',
        label='Est actif'
    )
    
    # ───────────────────────────────────────────────────────
    # TEXT SEARCH FILTERS
    # ───────────────────────────────────────────────────────
    
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Nom'
    )
    
    support_email = django_filters.CharFilter(
        field_name='support_email',
        lookup_expr='icontains',
        label='Email support'
    )
    
    search = django_filters.CharFilter(
        method='filter_search',
        label='Recherche globale'
    )
    
    # ───────────────────────────────────────────────────────
    # CUSTOM FILTER METHODS
    # ───────────────────────────────────────────────────────
    
    def filter_search(self, queryset, name, value):
        """
        Recherche globale multi-champs
        
        Cherche dans :
        - name
        - support_email
        - notes
        
        Usage :
        GET /suppliers/?search=Microsoft
        """
        return queryset.filter(
            Q(name__icontains=value) |
            Q(support_email__icontains=value) |
            Q(notes__icontains=value)
        ).distinct()
    
    # ───────────────────────────────────────────────────────
    # META
    # ───────────────────────────────────────────────────────
    
    class Meta:
        model = Supplier
        fields = {
            'type': ['exact'],
            'is_active': ['exact'],
            'name': ['icontains', 'iexact'],
            'created_at': ['gte', 'lte'],
        }


# ═══════════════════════════════════════════════════════════
# ORDERING FILTER
# ═══════════════════════════════════════════════════════════

class SupplierOrderingFilter(django_filters.OrderingFilter):
    """
    Filtre de tri personnalisé
    
    Usage :
    GET /suppliers/?ordering=name
    GET /suppliers/?ordering=-created_at (DESC)
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.extra['choices'] = [
            ('name', 'Nom (A-Z)'),
            ('-name', 'Nom (Z-A)'),
            ('type', 'Type (A-Z)'),
            ('-type', 'Type (Z-A)'),
            ('created_at', 'Date création (anciens)'),
            ('-created_at', 'Date création (récents)'),
            ('updated_at', 'Date modification (anciens)'),
            ('-updated_at', 'Date modification (récents)'),
        ]