"""
SUBSCRIPTION SERIALIZERS

Serializers pour Subscriptions et SubscriptionTerms
"""

from rest_framework import serializers
from decimal import Decimal

from ..models import (
    Subscription,
    SubscriptionTerm,
    SubscriptionStatus,
)


# ═══════════════════════════════════════════════════════════
# SUBSCRIPTION TERM SERIALIZERS
# ═══════════════════════════════════════════════════════════

class SubscriptionTermSerializer(serializers.ModelSerializer):
    """
    Serializer SubscriptionTerm (terme de subscription)
    
    Usage:
        - Liste termes d'une subscription
        - Détail terme
    """
    
    # Relations (read-only)
    subscription_number = serializers.CharField(
        source='subscription.subscription_number',
        read_only=True
    )
    
    opportunity_reference = serializers.CharField(
        source='opportunity.reference',
        read_only=True
    )
    
    # Computed fields
    margin = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    margin_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    
    duration_days = serializers.IntegerField(read_only=True)
    
    # Status flags
    is_current = serializers.SerializerMethodField()
    is_past = serializers.SerializerMethodField()
    is_future = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionTerm
        fields = [
            'id',
            'subscription',
            'subscription_number',
            'opportunity',
            'opportunity_reference',
            'provision',
            'term_number',
            'start_date',
            'end_date',
            'unit_price_purchase',
            'unit_price_sale',
            'total_purchase',
            'total_sale',
            'margin',
            'margin_percent',
            'duration_days',
            'is_current',
            'is_past',
            'is_future',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'total_purchase',
            'total_sale',
            'margin',
            'margin_percent',
            'created_at',
        ]
    
    def get_is_current(self, obj):
        """Check if term is current"""
        return obj.is_current()
    
    def get_is_past(self, obj):
        """Check if term is past"""
        return obj.is_past()
    
    def get_is_future(self, obj):
        """Check if term is future"""
        return obj.is_future()


# ═══════════════════════════════════════════════════════════
# SUBSCRIPTION SERIALIZERS
# ═══════════════════════════════════════════════════════════

class SubscriptionListSerializer(serializers.ModelSerializer):
    """
    Serializer liste Subscriptions (léger)
    
    Usage:
        - GET /subscriptions/
    """
    
    # Relations
    client_name = serializers.CharField(
        source='client.company_name',
        read_only=True
    )
    
    product_title = serializers.CharField(
        source='product.title',
        read_only=True
    )
    
    # Status display
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    billing_cycle_display = serializers.CharField(
        source='get_billing_cycle_display',
        read_only=True
    )
    
    # Computed
    days_until_expiration = serializers.IntegerField(read_only=True)
    is_expiring_soon = serializers.SerializerMethodField()
    
    # Current term info
    current_term = SubscriptionTermSerializer(
        source='get_current_term',
        read_only=True
    )
    
    class Meta:
        model = Subscription
        fields = [
            'id',
            'subscription_number',
            'client',
            'client_name',
            'product',
            'product_title',
            'quantity',
            'billing_cycle',
            'billing_cycle_display',
            'current_term_start',
            'current_term_end',
            'auto_renew',
            'status',
            'status_display',
            'days_until_expiration',
            'is_expiring_soon',
            'current_term',
            'created_at',
        ]
    
    def get_is_expiring_soon(self, obj):
        """Check if expiring in next 30 days"""
        return obj.is_expiring_soon(days=30)


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détail Subscription (complet)
    
    Usage:
        - GET /subscriptions/:id/
    """
    
    # Relations (nested)
    client = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    
    # Terms (nested)
    terms = SubscriptionTermSerializer(many=True, read_only=True)
    current_term = SubscriptionTermSerializer(
        source='get_current_term',
        read_only=True
    )
    latest_term = SubscriptionTermSerializer(
        source='get_latest_term',
        read_only=True
    )
    
    # Provisions (nested light)
    provisions = serializers.SerializerMethodField()
    
    # Status
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    billing_cycle_display = serializers.CharField(
        source='get_billing_cycle_display',
        read_only=True
    )
    
    # Computed
    days_until_expiration = serializers.IntegerField(read_only=True)
    is_expiring_soon = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    
    # Metrics
    revenue_metrics = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id',
            'subscription_number',
            'client',
            'product',
            'quantity',
            'billing_cycle',
            'billing_cycle_display',
            'provision',
            'current_term_start',
            'current_term_end',
            'auto_renew',
            'status',
            'status_display',
            'days_until_expiration',
            'is_expiring_soon',
            'is_active',
            'terms',
            'current_term',
            'latest_term',
            'provisions',
            'revenue_metrics',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'subscription_number',
            'status',
            'created_at',
            'updated_at',
        ]
    
    def get_client(self, obj):
        """Client info"""
        from ...clients.serializers import ClientListSerializer
        return ClientListSerializer(obj.client).data
    
    def get_product(self, obj):
        """Product info"""
        from ...products.serializers import ProductListSerializer
        return ProductListSerializer(obj.product).data
    
    def get_provisions(self, obj):
        """Provisions list (light)"""
        from .provision_serializers import ProvisionListSerializer
        provisions = obj.provisions.all().order_by('-created_at')
        return ProvisionListSerializer(provisions, many=True).data
    
    def get_is_expiring_soon(self, obj):
        """Check expiring"""
        return obj.is_expiring_soon(days=30)
    
    def get_revenue_metrics(self, obj):
        """Revenue metrics"""
        from ..services.subscription_service import get_subscription_revenue_metrics
        return get_subscription_revenue_metrics(obj)


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer création Subscription
    
    Usage:
        - POST /subscriptions/ (admin/test only)
    
    Note:
        Normalement créé via provision_service.complete_provisioning()
        Ce serializer pour tests/admin seulement
    """
    
    class Meta:
        model = Subscription
        fields = [
            'subscription_number',
            'client',
            'product',
            'quantity',
            'billing_cycle',
            'current_term_start',
            'current_term_end',
            'auto_renew',
        ]
    
    def validate(self, attrs):
        """Validation"""
        if attrs['current_term_end'] <= attrs['current_term_start']:
            raise serializers.ValidationError({
                'current_term_end': 'End date must be after start date'
            })
        
        return attrs


class SubscriptionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer update Subscription
    
    Usage:
        - PATCH /subscriptions/:id/
    
    Note:
        Seulement auto_renew modifiable
    """
    
    class Meta:
        model = Subscription
        fields = ['auto_renew']


# ═══════════════════════════════════════════════════════════
# RENEWAL SERIALIZERS
# ═══════════════════════════════════════════════════════════

class CreateRenewalSerializer(serializers.Serializer):
    """
    Serializer création opportunité renewal
    
    Usage:
        - POST /subscriptions/:id/create_renewal/
    
    Input:
        (vide - tout auto depuis subscription)
    
    Output:
        - opportunity: Opportunity créée
        - line: OpportunityLine créée
    """
    
    # Optionnel: modifier quantité
    quantity = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Nouvelle quantité (optionnel, sinon garde existante)"
    )
    
    # Optionnel: notes
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Notes opportunité renewal"
    )
    
    def validate_quantity(self, value):
        """Validate quantity"""
        if value and value < 1:
            raise serializers.ValidationError("Quantity must be >= 1")
        return value


class RenewalDataSerializer(serializers.Serializer):
    """
    Serializer données pré-remplies renewal
    
    Usage:
        - GET /subscriptions/:id/renewal_data/
    
    Output:
        Données pour pré-remplir form renewal
    """
    
    subscription_id = serializers.UUIDField(read_only=True)
    subscription_number = serializers.CharField(read_only=True)
    client_id = serializers.UUIDField(read_only=True)
    client_name = serializers.CharField(read_only=True)
    product_id = serializers.UUIDField(read_only=True)
    product_name = serializers.CharField(read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    billing_cycle = serializers.CharField(read_only=True)
    current_term_end = serializers.DateField(read_only=True)
    days_until_expiration = serializers.IntegerField(read_only=True)
    last_unit_price_purchase = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    last_unit_price_sale = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    original_opportunity_id = serializers.UUIDField(
        read_only=True,
        allow_null=True
    )
    original_opportunity_reference = serializers.CharField(
        read_only=True,
        allow_null=True
    )
    auto_renew = serializers.BooleanField(read_only=True)