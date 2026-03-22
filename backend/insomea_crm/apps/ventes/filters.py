"""
FILTERS - APP OPPORTUNITIES - MODIFIÉ

🆕 Ajout filtres type, related_opportunity
"""

import django_filters
from django.db.models import Q

from .models import (
    Opportunity,
    OpportunityLine,
    OpportunityStatus,
    OpportunityType,  # 🆕 NOUVEAU
    OpportunityLineStatus,
    SupplierQuote,
    InsomeaQuote,
    Provision,
    ProvisionStatus,
    Subscription,
    SubscriptionStatus,  # 🆕 NOUVEAU
    StatusHistory,
)


# ═══════════════════════════════════════════════════════════
# OPPORTUNITY FILTER
# ═══════════════════════════════════════════════════════════

class OpportunityFilter(django_filters.FilterSet):
    """
    Filters pour Opportunity
    
    🆕 MODIFIÉ: Ajout type, related_opportunity
    """
    
    # Status
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=OpportunityStatus.choices
    )
    
    # 🆕 NOUVEAU: Type
    type = django_filters.ChoiceFilter(
        field_name='type',
        choices=OpportunityType.choices
    )
    
    # Client
    client = django_filters.UUIDFilter(field_name='client__id')
    client_name = django_filters.CharFilter(
        field_name='client__company_name',
        lookup_expr='icontains'
    )
    
    # Assignation
    created_by = django_filters.UUIDFilter(field_name='created_by__id')
    assigned_to = django_filters.UUIDFilter(field_name='assigned_to__id')
    
    # 🆕 NOUVEAU: Related opportunity
    related_opportunity = django_filters.UUIDFilter(
        field_name='related_opportunity__id'
    )
    
    # Dates
    created_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    # Search (combiné reference + name)
    search = django_filters.CharFilter(method='filter_search')
    
    def filter_search(self, queryset, name, value):
        """Recherche dans reference, name, client"""
        return queryset.filter(
            Q(reference__icontains=value) |
            Q(name__icontains=value) |
            Q(client__company_name__icontains=value)
        )
    
    class Meta:
        model = Opportunity
        fields = [
            'status',
            'type',  # 🆕 NOUVEAU
            'client',
            'created_by',
            'assigned_to',
            'related_opportunity',  # 🆕 NOUVEAU
        ]


# ═══════════════════════════════════════════════════════════
# OPPORTUNITYLINE FILTER (INCHANGÉ)
# ═══════════════════════════════════════════════════════════

class OpportunityLineFilter(django_filters.FilterSet):
    """Filters pour OpportunityLine"""
    
    opportunity = django_filters.UUIDFilter(field_name='opportunity__id')
    product = django_filters.UUIDFilter(field_name='product__id')
    product_name = django_filters.CharFilter(
        field_name='product__title',
        lookup_expr='icontains'
    )
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=OpportunityLineStatus.choices
    )
    billing_cycle = django_filters.CharFilter(field_name='billing_cycle')
    
    class Meta:
        model = OpportunityLine
        fields = ['opportunity', 'product', 'status', 'billing_cycle']


# ═══════════════════════════════════════════════════════════
# SUBSCRIPTION FILTER
# ═══════════════════════════════════════════════════════════

class SubscriptionFilter(django_filters.FilterSet):
    """
    Filters pour Subscription
    
    🆕 NOUVEAU
    """
    
    # Status
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=SubscriptionStatus.choices
    )
    
    # Client
    client = django_filters.UUIDFilter(field_name='client__id')
    client_name = django_filters.CharFilter(
        field_name='client__company_name',
        lookup_expr='icontains'
    )
    
    # Product
    product = django_filters.UUIDFilter(field_name='product__id')
    product_name = django_filters.CharFilter(
        field_name='product__title',
        lookup_expr='icontains'
    )
    
    # Billing cycle
    billing_cycle = django_filters.CharFilter(field_name='billing_cycle')
    
    # Auto renew
    auto_renew = django_filters.BooleanFilter(field_name='auto_renew')
    
    # Dates
    term_end_after = django_filters.DateFilter(
        field_name='current_term_end',
        lookup_expr='gte'
    )
    term_end_before = django_filters.DateFilter(
        field_name='current_term_end',
        lookup_expr='lte'
    )
    
    # Search
    search = django_filters.CharFilter(method='filter_search')
    
    def filter_search(self, queryset, name, value):
        """Recherche dans subscription_number, client, product"""
        return queryset.filter(
            Q(subscription_number__icontains=value) |
            Q(client__company_name__icontains=value) |
            Q(product__title__icontains=value)
        )
    
    class Meta:
        model = Subscription
        fields = [
            'status',
            'client',
            'product',
            'billing_cycle',
            'auto_renew',
        ]


# ═══════════════════════════════════════════════════════════
# AUTRES FILTERS (INCHANGÉS)
# ═══════════════════════════════════════════════════════════

class SupplierQuoteFilter(django_filters.FilterSet):
    """Filters pour SupplierQuote"""
    
    supplier = django_filters.UUIDFilter(field_name='supplier__id')
    supplier_name = django_filters.CharFilter(
        field_name='supplier__name',
        lookup_expr='icontains'
    )
    opportunity = django_filters.UUIDFilter(
        field_name='lines__opportunity_line__opportunity__id'
    )
    received_after = django_filters.DateFilter(
        field_name='received_at',
        lookup_expr='gte'
    )
    received_before = django_filters.DateFilter(
        field_name='received_at',
        lookup_expr='lte'
    )
    
    class Meta:
        model = SupplierQuote
        fields = ['supplier', 'opportunity']


class InsomeaQuoteFilter(django_filters.FilterSet):
    """Filters pour InsomeaQuote"""
    
    opportunity = django_filters.UUIDFilter(field_name='opportunity__id')
    client = django_filters.UUIDFilter(field_name='opportunity__client__id')
    created_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    class Meta:
        model = InsomeaQuote
        fields = ['opportunity', 'client']


class ProvisionFilter(django_filters.FilterSet):
    """Filters pour Provision"""
    
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=ProvisionStatus.choices
    )
    opportunity = django_filters.UUIDFilter(
        field_name='opportunity_line__opportunity__id'
    )
    provisionned_by = django_filters.UUIDFilter(field_name='provisionned_by__id')
    product = django_filters.UUIDFilter(
        field_name='opportunity_line__product__id'
    )
    
    # 🆕 NOUVEAU: Filter by subscription (renewal vs initial)
    subscription = django_filters.UUIDFilter(field_name='subscription__id')
    is_renewal = django_filters.BooleanFilter(method='filter_is_renewal')
    
    def filter_is_renewal(self, queryset, name, value):
        """Filter renewal vs initial provisions"""
        if value:
            return queryset.filter(subscription__isnull=False)
        else:
            return queryset.filter(subscription__isnull=True)
    
    class Meta:
        model = Provision
        fields = ['status', 'opportunity', 'provisionned_by', 'product', 'subscription']


class StatusHistoryFilter(django_filters.FilterSet):
    """Filters pour StatusHistory"""
    
    opportunity = django_filters.UUIDFilter(field_name='opportunity__id')
    opportunity_line = django_filters.UUIDFilter(field_name='opportunity_line__id')
    provision = django_filters.UUIDFilter(field_name='provision__id')
    changed_by = django_filters.UUIDFilter(field_name='changed_by__id')
    transition_name = django_filters.CharFilter(field_name='transition_name')
    status_precedent = django_filters.CharFilter(field_name='status_precedent')
    status_suivant = django_filters.CharFilter(field_name='status_suivant')
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    class Meta:
        model = StatusHistory
        fields = [
            'opportunity',
            'opportunity_line',
            'provision',
            'changed_by',
            'transition_name',
        ]