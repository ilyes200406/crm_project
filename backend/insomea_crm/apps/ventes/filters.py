"""
FILTERS - APP OPPORTUNITIES

Django-filter FilterSets
"""

import django_filters
from django.db.models import Q

from .models import (
    Opportunity,
    OpportunityLine,
    OpportunityStatus,
    OpportunityLineStatus,
    SupplierQuote,
    InsomeaQuote,
    Provision,
    ProvisionStatus,
    Subscription,
    StatusHistory,
)


class OpportunityFilter(django_filters.FilterSet):
    """
    Filters pour Opportunity
    
    Usage:
        GET /opportunities/?status=DRAFT&client=uuid&created_after=2024-01-01
    """
    
    # Status
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=OpportunityStatus.choices
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
            'client',
            'created_by',
            'assigned_to',
        ]


class OpportunityLineFilter(django_filters.FilterSet):
    """
    Filters pour OpportunityLine
    """
    
    # Opportunity
    opportunity = django_filters.UUIDFilter(field_name='opportunity__id')
    
    # Product
    product = django_filters.UUIDFilter(field_name='product__id')
    product_name = django_filters.CharFilter(
        field_name='product__title',
        lookup_expr='icontains'
    )
    
    # Status
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=OpportunityLineStatus.choices
    )
    
    # Billing cycle
    billing_cycle = django_filters.CharFilter(field_name='billing_cycle')
    
    class Meta:
        model = OpportunityLine
        fields = ['opportunity', 'product', 'status', 'billing_cycle']


class SupplierQuoteFilter(django_filters.FilterSet):
    """
    Filters pour SupplierQuote
    """
    
    # Supplier
    supplier = django_filters.UUIDFilter(field_name='supplier__id')
    supplier_name = django_filters.CharFilter(
        field_name='supplier__name',
        lookup_expr='icontains'
    )
    
    # Opportunity (via lines)
    opportunity = django_filters.UUIDFilter(
        field_name='lines__opportunity_line__opportunity__id'
    )
    
    # Dates
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
    """
    Filters pour InsomeaQuote
    """
    
    # Opportunity
    opportunity = django_filters.UUIDFilter(field_name='opportunity__id')
    
    # Client (via opportunity)
    client = django_filters.UUIDFilter(field_name='opportunity__client__id')
    
    # Dates
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
    """
    Filters pour Provision
    """
    
    # Status
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=ProvisionStatus.choices
    )
    
    # Opportunity
    opportunity = django_filters.UUIDFilter(
        field_name='opportunity_line__opportunity__id'
    )
    
    # Technicien
    provisionned_by = django_filters.UUIDFilter(field_name='provisionned_by__id')
    
    # Product
    product = django_filters.UUIDFilter(
        field_name='opportunity_line__product__id'
    )
    
    class Meta:
        model = Provision
        fields = ['status', 'opportunity', 'provisionned_by', 'product']


class SubscriptionFilter(django_filters.FilterSet):
    """
    Filters pour Subscription
    """
    
    # Opportunity
    opportunity = django_filters.UUIDFilter(
        field_name='provision__opportunity_line__opportunity__id'
    )
    
    # Product
    product = django_filters.UUIDFilter(
        field_name='provision__opportunity_line__product__id'
    )
    
    # Technicien
    provisionned_by = django_filters.UUIDFilter(
        field_name='provision__provisionned_by__id'
    )
    
    # Dates
    start_after = django_filters.DateFilter(
        field_name='start_date',
        lookup_expr='gte'
    )
    end_before = django_filters.DateFilter(
        field_name='end_date',
        lookup_expr='lte'
    )
    
    # Active
    is_active = django_filters.BooleanFilter(method='filter_is_active')
    
    def filter_is_active(self, queryset, name, value):
        """Filtre subscriptions actives"""
        from datetime import date
        today = date.today()
        
        if value:
            return queryset.filter(
                start_date__lte=today,
                end_date__gte=today
            )
        else:
            return queryset.exclude(
                start_date__lte=today,
                end_date__gte=today
            )
    
    class Meta:
        model = Subscription
        fields = ['opportunity', 'product', 'provisionned_by']


class StatusHistoryFilter(django_filters.FilterSet):
    """
    Filters pour StatusHistory
    """
    
    # Opportunity
    opportunity = django_filters.UUIDFilter(field_name='opportunity__id')
    
    # OpportunityLine
    opportunity_line = django_filters.UUIDFilter(field_name='opportunity_line__id')
    
    # Provision
    provision = django_filters.UUIDFilter(field_name='provision__id')
    
    # User
    changed_by = django_filters.UUIDFilter(field_name='changed_by__id')
    
    # Transition
    transition_name = django_filters.CharFilter(field_name='transition_name')
    
    # Status
    status_precedent = django_filters.CharFilter(field_name='status_precedent')
    status_suivant = django_filters.CharFilter(field_name='status_suivant')
    
    # Dates
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