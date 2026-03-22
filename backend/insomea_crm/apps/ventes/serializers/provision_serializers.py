"""
PROVISION SERIALIZERS

Transformation Provision & Subscription ↔ JSON
"""

from rest_framework import serializers
from datetime import date

from ..models import Provision, ProvisionStatus, Subscription
from ..validators import validate_can_start_provisioning

# Import serializers
from ...users.api.serializers import UserMinimalSerializer


# ═══════════════════════════════════════════════════════════
# PROVISION
# ═══════════════════════════════════════════════════════════

class ProvisionMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer minimal Provision (pour nested)
    """
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    provisionned_by = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = Provision
        fields = [
            'id',
            'status',
            'status_display',
            'provisionned_by',
            'provisioning_started_at',
            'provisioning_completed_at',
        ]
        read_only_fields = fields


class ProvisionSerializer(serializers.ModelSerializer):
    """
    Serializer complet Provision
    
    Usage:
        GET /provisions/
        GET /provisions/{id}/
    """
    
    opportunity_line = serializers.SerializerMethodField()
    provisionned_by = UserMinimalSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Subscription nested (si existe)
    subscription = serializers.SerializerMethodField()
    
    class Meta:
        model = Provision
        fields = [
            'id',
            'opportunity_line',
            'status',
            'status_display',
            'provisionned_by',
            'microsoft_subscription_id',
            'provisioning_started_at',
            'provisioning_completed_at',
            'provisioning_error',
            'subscription',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_opportunity_line(self, obj):
        """Retourne OpportunityLine avec product"""
        if obj.opportunity_line:
            from .line_serializers import OpportunityLineMinimalSerializer
            return OpportunityLineMinimalSerializer(
                obj.opportunity_line,
                context=self.context
            ).data
        return None
    
    def get_subscription(self, obj):
        """Retourne Subscription si existe"""
        if hasattr(obj, 'subscription') and obj.subscription:
            return SubscriptionSerializer(
                obj.subscription,
                context=self.context
            ).data
        return None


# ═══════════════════════════════════════════════════════════
# PROVISION ACTIONS
# ═══════════════════════════════════════════════════════════

class StartProvisioningSerializer(serializers.Serializer):
    """
    Serializer action: Démarrer provisionnement
    
    Usage:
        POST /provisions/{id}/start/
    
    Input: {} (vide, user récupéré depuis request)
    """
    
    # Pas de fields requis (user depuis request.user)
    pass


class CompleteProvisioningSerializer(serializers.Serializer):
    """
    Serializer action: Terminer provisionnement
    
    Usage:
        POST /provisions/{id}/complete/
    
    Input:
        {
            "subscription_number": "abc-123-def",
            "start_date": "2024-01-01",
            "end_date": "2025-01-01"
        }
    """
    
    subscription_number = serializers.CharField(
        max_length=200,
        help_text="ID Microsoft subscription"
    )
    
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    def validate_subscription_number(self, value):
        """Valide unicité"""
        if Subscription.objects.filter(subscription_number=value).exists():
            raise serializers.ValidationError(
                f'Subscription {value} existe déjà'
            )
        return value
    
    def validate(self, data):
        """Valide dates"""
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError({
                'end_date': 'end_date doit être après start_date'
            })
        
        # Vérifie dates cohérentes (end_date pas trop loin)
        from datetime import timedelta
        max_duration = timedelta(days=5*365)  # 5 ans max
        
        if data['end_date'] - data['start_date'] > max_duration:
            raise serializers.ValidationError({
                'end_date': 'Durée subscription trop longue (max 5 ans)'
            })
        
        return data


class FailProvisioningSerializer(serializers.Serializer):
    """
    Serializer action: Marquer provisionnement échoué
    
    Usage:
        POST /provisions/{id}/fail/
    
    Input:
        {
            "error_message": "Microsoft API timeout"
        }
    """
    
    error_message = serializers.CharField(
        max_length=1000,
        help_text="Message d'erreur détaillé"
    )


# ═══════════════════════════════════════════════════════════
# SUBSCRIPTION
# ═══════════════════════════════════════════════════════════

class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer Subscription
    
    Usage:
        GET /subscriptions/
        GET /subscriptions/{id}/
    """
    
    provision = ProvisionMinimalSerializer(read_only=True)
    
    # Helpers
    is_active = serializers.SerializerMethodField()
    days_until_expiration = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id',
            'provision',
            'subscription_number',
            'start_date',
            'end_date',
            'is_active',
            'days_until_expiration',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_is_active(self, obj):
        """Vérifie si subscription active"""
        today = date.today()
        return obj.start_date <= today <= obj.end_date
    
    def get_days_until_expiration(self, obj):
        """Jours jusqu'à expiration"""
        today = date.today()
        if obj.end_date < today:
            return 0  # Expirée
        delta = obj.end_date - today
        return delta.days