"""
OPPORTUNITY LINE SERIALIZERS

Transformation OpportunityLine ↔ JSON
"""

from rest_framework import serializers

from ..models import OpportunityLine, OpportunityLineStatus, BillingCycle
from ..validators import (
    validate_opportunity_line_data,
    validate_quantity,
    validate_product_unique_in_opportunity,
)

# Import serializers from other apps
from ...products.serializers import ProductMinimalSerializer


# ═══════════════════════════════════════════════════════════
# MINIMAL (pour nested)
# ═══════════════════════════════════════════════════════════

class OpportunityLineMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer minimal ligne (pour nested)
    
    Usage:
        - Nested dans OpportunityDetailSerializer
        - Références dans quotes, provisions
    """
    
    product = ProductMinimalSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = OpportunityLine
        fields = [
            'id',
            'product',
            'quantity',
            'billing_cycle',
            'status',
            'status_display',
            'created_at',
        ]
        read_only_fields = fields


# ═══════════════════════════════════════════════════════════
# DETAIL
# ═══════════════════════════════════════════════════════════

class OpportunityLineSerializer(serializers.ModelSerializer):
    """
    Serializer complet ligne
    
    Usage:
        GET /opportunity-lines/{id}/
    """
    
    product = ProductMinimalSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Relations optionnelles (si préchargées)
    supplier_quote_line = serializers.SerializerMethodField()
    insomea_quote_line = serializers.SerializerMethodField()
    provision = serializers.SerializerMethodField()
    insomea_purchase_order = serializers.SerializerMethodField()
    
    # Helpers
    has_supplier_quote = serializers.BooleanField(read_only=True, source='has_supplier_quote')
    
    class Meta:
        model = OpportunityLine
        fields = [
            'id',
            'product',
            'quantity',
            'billing_cycle',
            'status',
            'status_display',
            'notes',
            
            # Relations
            'supplier_quote_line',
            'insomea_quote_line',
            'provision',
            'insomea_purchase_order',
            
            # Helpers
            'has_supplier_quote',
            
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'status_display',
            'created_at',
            'updated_at',
        ]
    
    def get_supplier_quote_line(self, obj):
        """Retourne SupplierQuoteLine si existe"""
        if hasattr(obj, 'supplier_quote_line') and obj.supplier_quote_line:
            from .quote_serializers import SupplierQuoteLineSerializer
            return SupplierQuoteLineSerializer(
                obj.supplier_quote_line,
                context=self.context
            ).data
        return None
    
    def get_insomea_quote_line(self, obj):
        """Retourne InsomeaQuoteLine si existe"""
        if hasattr(obj, 'insomea_quote_line') and obj.insomea_quote_line:
            from .quote_serializers import InsomeaQuoteLineSerializer
            return InsomeaQuoteLineSerializer(
                obj.insomea_quote_line,
                context=self.context
            ).data
        return None
    
    def get_provision(self, obj):
        """Retourne Provision si existe"""
        if hasattr(obj, 'provision') and obj.provision:
            from .provision_serializers import ProvisionMinimalSerializer
            return ProvisionMinimalSerializer(
                obj.provision,
                context=self.context
            ).data
        return None
    
    def get_insomea_purchase_order(self, obj):
        """Retourne InsomeaPO si lié"""
        if obj.insomea_purchase_order:
            from .workflow_serializers import InsomeaPOSerializer
            return InsomeaPOSerializer(
                obj.insomea_purchase_order,
                context=self.context
            ).data
        return None


# ═══════════════════════════════════════════════════════════
# CREATE
# ═══════════════════════════════════════════════════════════

class OpportunityLineCreateSerializer(serializers.Serializer):
    """
    Serializer pour création ligne
    
    Usage:
        POST /opportunities/{id}/lines/
        POST /opportunity-lines/
    
    Note:
        Utilise Serializer (pas ModelSerializer) pour contrôle total validation
    """
    
    opportunity_id = serializers.UUIDField(
        write_only=True,
        required=False,
        help_text="UUID Opportunity (requis si POST direct sur /opportunity-lines/)"
    )
    
    product_id = serializers.UUIDField(write_only=True)
    
    quantity = serializers.IntegerField(min_value=1, max_value=10000)
    
    billing_cycle = serializers.ChoiceField(
        choices=BillingCycle.choices,
        default=BillingCycle.ANNUAL
    )
    
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000
    )
    
    def validate_product_id(self, value):
        """Valide que produit existe"""
        from ...products.models import Product
        
        try:
            product = Product.objects.get(id=value)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError('Produit introuvable')
    
    def validate_quantity(self, value):
        """Valide quantité"""
        validate_quantity(value)
        return value
    
    def validate(self, data):
        """Validation globale"""
        
        # Récupère product
        from ...products.models import Product
        product = Product.objects.get(id=data['product_id'])
        data['product'] = product
        
        # Récupère opportunity (depuis context ou data)
        opportunity = self.context.get('opportunity')
        if not opportunity and 'opportunity_id' in data:
            from ..models import Opportunity
            try:
                opportunity = Opportunity.objects.get(id=data['opportunity_id'])
            except Opportunity.DoesNotExist:
                raise serializers.ValidationError({
                    'opportunity_id': 'Opportunité introuvable'
                })
        
        if not opportunity:
            raise serializers.ValidationError({
                'opportunity_id': 'Opportunité requise'
            })
        
        # Validation métier
        validate_opportunity_line_data(data, opportunity=opportunity)
        
        return data
    
    def create(self, validated_data):
        """
        NE PAS utiliser directement
        
        Utiliser le service: add_line_to_opportunity()
        """
        raise NotImplementedError(
            'Utiliser opportunities.services.add_line_to_opportunity()'
        )


# ═══════════════════════════════════════════════════════════
# UPDATE
# ═══════════════════════════════════════════════════════════

class OpportunityLineUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour mise à jour ligne
    
    Usage:
        PUT/PATCH /opportunity-lines/{id}/
    """
    
    class Meta:
        model = OpportunityLine
        fields = [
            'quantity',
            'billing_cycle',
            'notes',
        ]
    
    def validate_quantity(self, value):
        """Valide quantité"""
        validate_quantity(value)
        return value
    
    def validate(self, data):
        """Validation globale"""
        opportunity = self.instance.opportunity
        validate_opportunity_line_data(data, opportunity=opportunity, line=self.instance)
        return data
    
    def update(self, instance, validated_data):
        """
        NE PAS utiliser directement
        
        Utiliser le service: update_opportunity_line()
        """
        raise NotImplementedError(
            'Utiliser opportunities.services.update_opportunity_line()'
        )