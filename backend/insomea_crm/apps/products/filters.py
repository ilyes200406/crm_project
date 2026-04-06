"""FILTERS - APP PRODUCTS"""

import django_filters
from django.db.models import Q
from .models import Product


class ProductFilter(django_filters.FilterSet):
    """Filtres products"""
    
    category = django_filters.ChoiceFilter(field_name='category')
    supplier = django_filters.UUIDFilter(field_name='supplier__id')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    is_deprecated = django_filters.BooleanFilter(field_name='is_deprecated')
    
    sku = django_filters.CharFilter(field_name='sku', lookup_expr='icontains')
    name = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    
    search = django_filters.CharFilter(method='filter_search')
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(sku__icontains=value) |
            Q(title__icontains=value) |
            Q(description_commerciale__icontains=value)
        )
    
    class Meta:
        model = Product
        fields = ['category', 'supplier', 'is_active', 'is_deprecated']