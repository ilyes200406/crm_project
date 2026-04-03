"""ADMIN - APP PRODUCTS"""

from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'title', 'version', 'category', 'supplier', 'is_active']
    list_filter = ['category', 'is_active', 'is_deprecated', 'supplier']
    search_fields = ['sku', 'title']
    ordering = ['title']
