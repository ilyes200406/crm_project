"""SERIALIZERS - APP PRODUCTS"""

from rest_framework import serializers
from .models import Product
from suppliers.serializers import SupplierMinimalSerializer


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer liste products (léger)"""
    
    supplier = SupplierMinimalSerializer(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'version', 'category', 'category_display',
            'supplier', 'is_active', 'is_deprecated', 'created_at'
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer détails product (complet)"""
    
    supplier = SupplierMinimalSerializer(read_only=True)
    successor = ProductListSerializer(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer création product"""
    
    class Meta:
        model = Product
        fields = [
            'sku', 'name', 'version', 'category', 'description_technique',
            'description_commerciale', 'supplier'
        ]
    
    def validate(self, data):
        from .validators import validate_product_data
        validate_product_data(data)
        return data


class ProductMinimalSerializer(serializers.ModelSerializer):
    """Serializer minimal (pour nested)"""
    
    class Meta:
        model = Product
        fields = ['id', 'sku', 'name', 'version']