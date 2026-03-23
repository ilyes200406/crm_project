"""
OPPORTUNITY LINE SERIALIZERS - MODIFIÉ

Support renewal workflow
"""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from ..models import OpportunityLine, OpportunityLineStatus, BillingCycle
from ..validators import (
    validate_quantity,
    validate_line_editable,
)


# ═══════════════════════════════════════════════════════════
# OPPORTUNITYLINE LIST SERIALIZER
# ═══════════════════════════════════════════════════════════

class OpportunityLineListSerializer(serializers.ModelSerializer):
    """
    Serializer liste OpportunityLines (léger)
    """
    
    # Relations
    product_title = serializers.CharField(
        source='product.title',
        read_only=True
    )
    
    opportunity_reference = serializers.CharField(
        source='opportunity.reference',
        read_only=True
    )
    
    # 🆕 NOUVEAU: Renewal info
    renewal_of_subscription_number = serializers.CharField(
        source='renewal_of_subscription.subscription_number',
        read_only=True,
        allow_null=True
    )
    
    # Status
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    billing_cycle_display = serializers.CharField(
        source='get_billing_cycle_display',
        read_only=True
    )
    
    # Pricing (from InsomeaQuoteLine if exists)
    unit_price_purchase = serializers.SerializerMethodField()
    unit_price_sale = serializers.SerializerMethodField()
    total_purchase = serializers.SerializerMethodField()
    total_sale = serializers.SerializerMethodField()
    margin = serializers.SerializerMethodField()
    
    # 🆕 NOUVEAU: Flags
    is_renewal = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = OpportunityLine
        fields = [
            'id',
            'opportunity',
            'opportunity_reference',
            'product',
            'product_title',
            'quantity',
            'billing_cycle',
            'billing_cycle_display',
            'renewal_of_subscription',  # 🆕 NOUVEAU
            'renewal_of_subscription_number',  # 🆕 NOUVEAU
            'status',
            'status_display',
            'unit_price_purchase',
            'unit_price_sale',
            'total_purchase',
            'total_sale',
            'margin',
            'is_renewal',  # 🆕 NOUVEAU
            'notes',
            'created_at',
        ]
    
    def _get_quote_line(self, obj):
        try:
            return obj.insomea_quote_line
        except obj.__class__.insomea_quote_line.RelatedObjectDoesNotExist:
            return None
    
    def get_unit_price_purchase(self, obj):
        """Get price from InsomeaQuoteLine"""
        quote_line = self._get_quote_line(obj)
        if quote_line:
            return quote_line.unit_price_purchase
        return None
    
    def get_unit_price_sale(self, obj):
        """Get price from InsomeaQuoteLine"""
        quote_line = self._get_quote_line(obj)
        if quote_line:
            return quote_line.unit_price_sale
        return None
    
    def get_total_purchase(self, obj):
        """Get total from InsomeaQuoteLine"""
        quote_line = self._get_quote_line(obj)
        if quote_line:
            return quote_line.line_total_purchase
        return None
    
    def get_total_sale(self, obj):
        """Get total from InsomeaQuoteLine"""
        quote_line = self._get_quote_line(obj)
        if quote_line:
            return quote_line.line_total_sale
        return None
    
    def get_margin(self, obj):
        """Get margin from InsomeaQuoteLine"""
        quote_line = self._get_quote_line(obj)
        if quote_line:
            return quote_line.line_margin
        return None


# ═══════════════════════════════════════════════════════════
# OPPORTUNITYLINE DETAIL SERIALIZER
# ═══════════════════════════════════════════════════════════

class OpportunityLineDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détail OpportunityLine (complet)
    """
    
    # Relations (nested)
    product = serializers.SerializerMethodField()
    opportunity = serializers.SerializerMethodField()
    
    # 🆕 NOUVEAU: Renewal subscription (nested)
    renewal_of_subscription = serializers.SerializerMethodField()
    
    # Quotes
    supplier_quote_line = serializers.SerializerMethodField()
    insomea_quote_line = serializers.SerializerMethodField()
    
    # Provision
    provision = serializers.SerializerMethodField()
    
    # Status
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    billing_cycle_display = serializers.CharField(
        source='get_billing_cycle_display',
        read_only=True
    )
    
    # 🆕 NOUVEAU: Flags
    is_renewal = serializers.BooleanField(read_only=True)
    
    # Permissions
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = OpportunityLine
        fields = [
            'id',
            'opportunity',
            'product',
            'quantity',
            'billing_cycle',
            'billing_cycle_display',
            'renewal_of_subscription',  # 🆕 NOUVEAU
            'insomea_purchase_order',
            'status',
            'status_display',
            'supplier_quote_line',
            'insomea_quote_line',
            'provision',
            'is_renewal',  # 🆕 NOUVEAU
            'notes',
            'can_edit',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'created_at',
            'updated_at',
        ]
    
    def get_product(self, obj):
        """Product info"""
        from ...products.serializers import ProductDetailSerializer
        return ProductDetailSerializer(obj.product).data
    
    def get_opportunity(self, obj):
        """Opportunity info (light)"""
        from .opportunity_serializers import OpportunityListSerializer
        return OpportunityListSerializer(obj.opportunity).data
    
    # 🆕 NOUVEAU
    def get_renewal_of_subscription(self, obj):
        """Original subscription (si renewal)"""
        if obj.renewal_of_subscription:
            from .subscription_serializers import SubscriptionListSerializer
            return SubscriptionListSerializer(obj.renewal_of_subscription).data
        return None


    def _get_related(self, obj, field_name):
        try:
            return getattr(obj, field_name)
        except (AttributeError, ObjectDoesNotExist):
            return None


    def get_supplier_quote_line(self, obj):
        """SupplierQuoteLine"""
        quote_line = self._get_related(obj, 'supplier_quote_line')
        if quote_line:
            from .quote_serializers import SupplierQuoteLineSerializer
            return SupplierQuoteLineSerializer(obj.supplier_quote_line).data
        return None
    
    def get_provision(self, obj):
        """Provision"""
        provision = self._get_related(obj, 'provision')
        if provision:
            from .provision_serializers import ProvisionListSerializer
            return ProvisionListSerializer(obj.provision).data
        return None
    
    def get_insomea_quote_line(self, obj):
        """InsomeaQuoteLine"""
        quote_line = self._get_related(obj, 'insomea_quote_line')
        if quote_line:
            from .quote_serializers import InsomeaQuoteLineSerializer
            return InsomeaQuoteLineSerializer(obj.insomea_quote_line).data
        return None
    
    def get_can_edit(self, obj):
        """Check if can edit"""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        
        # Check if opportunity editable
        return obj.opportunity.can_edit()


class OpportunityLineMinimalSerializer(serializers.ModelSerializer):
    """Serializer minimal pour les imbrications légères."""

    product_title = serializers.CharField(source='product.title', read_only=True)

    class Meta:
        model = OpportunityLine
        fields = [
            'id',
            'product',
            'product_title',
            'quantity',
            'billing_cycle',
            'status',
        ]


class OpportunityLineSerializer(OpportunityLineDetailSerializer):
    """Alias backward-compatible pour le ViewSet lignes."""
    pass


# ═══════════════════════════════════════════════════════════
# OPPORTUNITYLINE CREATE/UPDATE SERIALIZERS
# ═══════════════════════════════════════════════════════════

class OpportunityLineCreateSerializer(serializers.ModelSerializer):
    """
    Serializer création OpportunityLine
    
    Usage:
        - POST /opportunity-lines/
        - Via add_line_to_opportunity service
    
    🆕 MODIFIÉ: renewal_of_subscription en read-only (géré par service)
    """
    
    class Meta:
        model = OpportunityLine
        fields = [
            'opportunity',
            'product',
            'quantity',
            'billing_cycle',
            'renewal_of_subscription',  # 🆕 NOUVEAU (read-only)
            'notes',
        ]
        read_only_fields = ['renewal_of_subscription']  # 🆕 Géré par service
    
    def validate_quantity(self, value):
        """Validate quantity"""
        validate_quantity(value)
        return value
    
    def validate(self, attrs):
        """Validation"""
        
        opportunity = attrs.get('opportunity')
        product = attrs.get('product')
        
        # Vérif duplicate product
        if OpportunityLine.objects.filter(
            opportunity=opportunity,
            product=product
        ).exists():
            raise serializers.ValidationError({
                'product': 'Product already exists in this opportunity'
            })
        
        return attrs


class OpportunityLineUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer update OpportunityLine
    
    Usage:
        - PATCH /opportunity-lines/:id/
    
    Note:
        renewal_of_subscription non modifiable
    """
    
    class Meta:
        model = OpportunityLine
        fields = [
            'quantity',
            'billing_cycle',
            'notes',
        ]
    
    def validate(self, attrs):
        """Validation"""
        line = self.instance
        
        # Check if editable
        validate_line_editable(line)
        
        return attrs
