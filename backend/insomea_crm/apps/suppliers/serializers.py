"""
SERIALIZERS - APP SUPPLIERS

Transformation données DB ↔ JSON

- SupplierListSerializer : Liste (léger)
- SupplierDetailSerializer : Détails complets
- SupplierCreateSerializer : Création avec validation
- SupplierUpdateSerializer : Mise à jour
"""

from rest_framework import serializers
from .models import Supplier, SupplierType
from .validators import (
    validate_supplier_data,
    normalize_supplier_name,
    normalize_phone_number,
    normalize_url,
)


# ═══════════════════════════════════════════════════════════
# SUPPLIER LIST SERIALIZER
# ═══════════════════════════════════════════════════════════

class SupplierListSerializer(serializers.ModelSerializer):
    """
    Serializer pour liste suppliers
    
    Usage :
    GET /suppliers/
    
    Léger pour performance
    Champs essentiels seulement
    """
    
    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True
    )
    
    class Meta:
        model = Supplier
        fields = [
            'id',
            'name',
            'type',
            'type_display',
            'support_email',
            'support_phone',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'type_display']


# ═══════════════════════════════════════════════════════════
# SUPPLIER DETAIL SERIALIZER
# ═══════════════════════════════════════════════════════════

class SupplierDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé pour un supplier
    
    Usage :
    GET /suppliers/{id}/
    
    Tous les champs
    """
    
    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True
    )
    
    class Meta:
        model = Supplier
        fields = [
            'id',
            'name',
            'type',
            'type_display',
            'website',
            'support_email',
            'support_phone',
            'notes',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'type_display',
        ]


# ═══════════════════════════════════════════════════════════
# SUPPLIER CREATE SERIALIZER
# ═══════════════════════════════════════════════════════════

class SupplierCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour création supplier
    
    Usage :
    POST /suppliers/
    
    Validation stricte
    Normalisation automatique
    """
    
    class Meta:
        model = Supplier
        fields = [
            'name',
            'type',
            'website',
            'support_email',
            'support_phone',
            'notes',
        ]
    
    def validate_name(self, value):
        """
        Valide et normalise nom
        
        Vérifications :
        - Format valide
        - Unicité (case-insensitive)
        """
        from .validators import validate_supplier_name, validate_supplier_unique_name
        
        # Valide format
        validate_supplier_name(value)
        
        # Normalise
        value = normalize_supplier_name(value)
        
        # Valide unicité
        validate_supplier_unique_name(value)
        
        return value
    
    def validate_support_email(self, value):
        """Valide email support"""
        if value:
            from .validators import validate_support_email
            validate_support_email(value)
        return value
    
    def validate_support_phone(self, value):
        """Valide et normalise téléphone"""
        if value:
            from .validators import validate_support_phone
            validate_support_phone(value)
            value = normalize_phone_number(value)
        return value
    
    def validate_website(self, value):
        """Valide et normalise URL"""
        if value:
            from .validators import validate_website_url
            validate_website_url(value)
            value = normalize_url(value)
        return value
    
    def validate(self, data):
        """Validation globale"""
        validate_supplier_data(data)
        return data


# ═══════════════════════════════════════════════════════════
# SUPPLIER UPDATE SERIALIZER
# ═══════════════════════════════════════════════════════════

class SupplierUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour mise à jour supplier
    
    Usage :
    PUT/PATCH /suppliers/{id}/
    
    Champs optionnels (partial update)
    """
    
    class Meta:
        model = Supplier
        fields = [
            'name',
            'type',
            'website',
            'support_email',
            'support_phone',
            'notes',
            'is_active',
        ]
    
    def validate_name(self, value):
        """Valide unicité nom (hors instance actuelle)"""
        from .validators import validate_supplier_name, validate_supplier_unique_name
        
        validate_supplier_name(value)
        
        value = normalize_supplier_name(value)
        
        # Valide unicité (exclut instance actuelle)
        instance = self.instance
        validate_supplier_unique_name(value, exclude_id=instance.id)
        
        return value
    
    def validate_support_email(self, value):
        """Valide email"""
        if value:
            from .validators import validate_support_email
            validate_support_email(value)
        return value
    
    def validate_support_phone(self, value):
        """Valide et normalise téléphone"""
        if value:
            from .validators import validate_support_phone
            validate_support_phone(value)
            value = normalize_phone_number(value)
        return value
    
    def validate_website(self, value):
        """Valide et normalise URL"""
        if value:
            from .validators import validate_website_url
            validate_website_url(value)
            value = normalize_url(value)
        return value
    
    def validate(self, data):
        """Validation globale"""
        validate_supplier_data(data, supplier=self.instance)
        return data


# ═══════════════════════════════════════════════════════════
# MINIMAL SERIALIZER (pour nested usage)
# ═══════════════════════════════════════════════════════════

class SupplierMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer minimal pour utilisation nested
    
    Usage :
    Dans Product, Opportunity, etc.
    """
    
    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True
    )
    
    class Meta:
        model = Supplier
        fields = [
            'id',
            'name',
            'type',
            'type_display',
        ]
        read_only_fields = fields


# ═══════════════════════════════════════════════════════════
# STATS SERIALIZER
# ═══════════════════════════════════════════════════════════

class SupplierStatsSerializer(serializers.Serializer):
    """
    Serializer pour statistiques suppliers
    
    Usage :
    GET /suppliers/stats/
    """
    
    total_suppliers = serializers.IntegerField()
    by_type = serializers.DictField(
        child=serializers.IntegerField()
    )
    active_count = serializers.IntegerField()
    inactive_count = serializers.IntegerField()