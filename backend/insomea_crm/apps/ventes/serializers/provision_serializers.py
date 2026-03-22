"""
PROVISION SERIALIZERS - MODIFIÉ
"""

from rest_framework import serializers
from ..models import Provision, ProvisionStatus


class ProvisionListSerializer(serializers.ModelSerializer):
    """
    Serializer liste Provisions (léger)
    """
    
    # Relations
    product_title = serializers.CharField(
        source='opportunity_line.product.title',
        read_only=True
    )
    
    client_name = serializers.CharField(
        source='opportunity_line.opportunity.client.company_name',
        read_only=True
    )
    
    opportunity_reference = serializers.CharField(
        source='opportunity_line.opportunity.reference',
        read_only=True
    )
    
    provisionned_by_name = serializers.CharField(
        source='provisionned_by.get_full_name',
        read_only=True,
        allow_null=True
    )
    
    # Status
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    # 🆕 NOUVEAU: Flags renewal
    is_renewal = serializers.BooleanField(read_only=True)
    is_initial = serializers.BooleanField(read_only=True)
    
    # 🆕 NOUVEAU: Subscription info (si existe)
    subscription_number = serializers.CharField(
        source='subscription.subscription_number',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Provision
        fields = [
            'id',
            'opportunity_line',
            'product_title',
            'client_name',
            'opportunity_reference',
            'subscription',  # 🆕 NOUVEAU
            'subscription_number',  # 🆕 NOUVEAU
            'subscription_term',  # 🆕 NOUVEAU
            'provisionned_by',
            'provisionned_by_name',
            'microsoft_subscription_id',
            'status',
            'status_display',
            'is_renewal',  # 🆕 NOUVEAU
            'is_initial',  # 🆕 NOUVEAU
            'provisioning_started_at',
            'provisioning_completed_at',
            'created_at',
        ]


class ProvisionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détail Provision (complet)
    """
    
    # Relations (nested)
    opportunity_line = serializers.SerializerMethodField()
    provisionned_by = serializers.SerializerMethodField()
    
    # 🆕 NOUVEAU: Subscription (nested si existe)
    subscription = serializers.SerializerMethodField()
    subscription_term = serializers.SerializerMethodField()
    
    # Status
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    # Flags
    is_renewal = serializers.BooleanField(read_only=True)
    is_initial = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Provision
        fields = [
            'id',
            'opportunity_line',
            'subscription',  # 🆕 NOUVEAU
            'subscription_term',  # 🆕 NOUVEAU
            'provisionned_by',
            'microsoft_subscription_id',
            'status',
            'status_display',
            'is_renewal',  # 🆕 NOUVEAU
            'is_initial',  # 🆕 NOUVEAU
            'provisioning_started_at',
            'provisioning_completed_at',
            'provisioning_error',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'created_at',
            'updated_at',
        ]
    
    def get_opportunity_line(self, obj):
        """OpportunityLine info"""
        from .line_serializers import OpportunityLineDetailSerializer
        return OpportunityLineDetailSerializer(obj.opportunity_line).data
    
    def get_provisionned_by(self, obj):
        """User info"""
        if obj.provisionned_by:
            from ...users.api.serializers import UserSerializer
            return UserSerializer(obj.provisionned_by).data
        return None
    
    def get_subscription(self, obj):
        """Subscription info (si existe)"""
        if obj.subscription:
            from .subscription_serializers import SubscriptionListSerializer
            return SubscriptionListSerializer(obj.subscription).data
        return None
    
    def get_subscription_term(self, obj):
        """SubscriptionTerm info (si existe)"""
        if obj.subscription_term:
            from .subscription_serializers import SubscriptionTermSerializer
            return SubscriptionTermSerializer(obj.subscription_term).data
        return None


class StartProvisioningSerializer(serializers.Serializer):
    """
    Serializer start provisioning
    
    Usage:
        POST /provisions/:id/start/
    
    Input: (vide)
    """
    pass


class CompleteProvisioningSerializer(serializers.Serializer):
    """
    Serializer complete provisioning
    
    🆕 MODIFIÉ: Support INITIAL vs RENEWAL
    
    Usage:
        POST /provisions/:id/complete/
    
    Input:
        CAS INITIAL:
        {
            "subscription_number": "MS-123",
            "start_date": "2024-01-01",
            "end_date": "2025-01-01"
        }
        
        CAS RENEWAL:
        {
            "start_date": "2025-01-01",
            "end_date": "2026-01-01"
            # PAS de subscription_number
        }
    """
    
    # 🆕 MODIFIÉ: Optionnel (requis seulement si INITIAL)
    subscription_number = serializers.CharField(
        required=False,
        max_length=200,
        help_text="Microsoft Subscription ID (requis si INITIAL)"
    )
    
    start_date = serializers.DateField(
        required=True,
        help_text="Date début terme"
    )
    
    end_date = serializers.DateField(
        required=True,
        help_text="Date fin terme"
    )
    
    def validate(self, attrs):
        """Validation"""
        
        # Vérifie dates
        if attrs['end_date'] <= attrs['start_date']:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date'
            })
        
        # 🆕 NOUVEAU: Vérifie subscription_number si INITIAL
        provision = self.context.get('provision')
        
        if provision and provision.is_initial():
            # INITIAL: subscription_number REQUIS
            if not attrs.get('subscription_number'):
                raise serializers.ValidationError({
                    'subscription_number': 'Required for initial provisioning'
                })
        else:
            # RENEWAL: subscription_number pas nécessaire
            if attrs.get('subscription_number'):
                raise serializers.ValidationError({
                    'subscription_number': 'Not allowed for renewal (subscription already exists)'
                })
        
        return attrs


class FailProvisioningSerializer(serializers.Serializer):
    """
    Serializer fail provisioning
    
    Usage:
        POST /provisions/:id/fail/
    """
    
    error_message = serializers.CharField(
        required=True,
        help_text="Error message"
    )