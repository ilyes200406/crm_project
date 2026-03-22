from rest_framework import serializers
from decimal import Decimal

from ..models import Opportunity, OpportunityStatus
from ..validators import (
    validate_opportunity_data,
    normalize_opportunity_name,
)

# Import serializers from other apps
from ...clients.serializers import ClientMinimalSerializer
from ...users.api.serializers import UserMinimalSerializer


# ═══════════════════════════════════════════════════════════
# MINIMAL (pour nested)
# ═══════════════════════════════════════════════════════════

class OpportunityMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer minimal Opportunity
    
    Usage:
        - Nested dans Provision, Subscription
        - Références croisées
    """
    
    client = ClientMinimalSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Opportunity
        fields = [
            'id',
            'reference',
            'name',
            'client',
            'status',
            'status_display',
            'created_at',
        ]
        read_only_fields = fields


# ═══════════════════════════════════════════════════════════
# LIST (léger, pour tableaux)
# ═══════════════════════════════════════════════════════════

class OpportunityListSerializer(serializers.ModelSerializer):
    """
    Serializer liste opportunities (léger)
    
    Usage:
        GET /opportunities/
    
    Optimisé pour performance
    """
    
    client = ClientMinimalSerializer(read_only=True)
    created_by = UserMinimalSerializer(read_only=True)
    assigned_to = UserMinimalSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Stats annotations (si préchargées par queryset)
    lines_count = serializers.IntegerField(read_only=True, required=False)
    
    class Meta:
        model = Opportunity
        fields = [
            'id',
            'reference',
            'name',
            'client',
            'created_by',
            'assigned_to',
            'status',
            'status_display',
            'lines_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


# ═══════════════════════════════════════════════════════════
# DETAIL (complet, avec relations)
# ═══════════════════════════════════════════════════════════

class OpportunityDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé opportunité
    
    Usage:
        GET /opportunities/{id}/
    
    Tous les champs + relations nested
    """
    
    client = ClientMinimalSerializer(read_only=True)
    created_by = UserMinimalSerializer(read_only=True)
    assigned_to = UserMinimalSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Relations nested (préchargées via prefetch_related)
    # NOTE: Importés dynamiquement pour éviter circular imports
    lines = serializers.SerializerMethodField()
    supplier_quotes = serializers.SerializerMethodField()
    insomea_quote = serializers.SerializerMethodField()
    client_purchase_order = serializers.SerializerMethodField()
    status_history = serializers.SerializerMethodField()
    
    # Stats
    lines_count = serializers.IntegerField(read_only=True, source='lines.count')
    
    # Helpers
    can_edit = serializers.BooleanField(read_only=True, source='can_edit')
    can_add_items = serializers.BooleanField(read_only=True, source='can_add_items')
    
    class Meta:
        model = Opportunity
        fields = [
            'id',
            'reference',
            'name',
            'client',
            'created_by',
            'assigned_to',
            'status',
            'status_display',
            
            # Relations
            'lines',
            'lines_count',
            'supplier_quotes',
            'insomea_quote',
            'client_purchase_order',
            'status_history',
            
            # Helpers
            'can_edit',
            'can_add_items',
            
            # Metadata
            'notes',
            'cancellation_reason',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'reference',
            'status',
            'status_display',
            'created_at',
            'updated_at',
        ]
    
    def get_lines(self, obj):
        """Retourne lignes (minimal)"""
        if hasattr(obj, 'lines'):
            from .line_serializers import OpportunityLineMinimalSerializer
            return OpportunityLineMinimalSerializer(
                obj.lines.all(),
                many=True,
                context=self.context
            ).data
        return []
    
    def get_supplier_quotes(self, obj):
        """Retourne devis fournisseurs (minimal)"""
        if hasattr(obj, 'supplier_quotes'):
            from .quote_serializers import SupplierQuoteSerializer
            return SupplierQuoteSerializer(
                obj.supplier_quotes.all(),
                many=True,
                context=self.context
            ).data
        return []
    
    def get_insomea_quote(self, obj):
        """Retourne devis Insomea (si existe)"""
        if hasattr(obj, 'insomea_quote') and obj.insomea_quote:
            from .quote_serializers import InsomeaQuoteSerializer
            return InsomeaQuoteSerializer(
                obj.insomea_quote,
                context=self.context
            ).data
        return None
    
    def get_client_purchase_order(self, obj):
        """Retourne BC client (si existe)"""
        if hasattr(obj, 'client_purchase_order') and obj.client_purchase_order:
            from .workflow_serializers import ClientPOSerializer
            return ClientPOSerializer(
                obj.client_purchase_order,
                context=self.context
            ).data
        return None
    
    def get_status_history(self, obj):
        """Retourne historique statuts (limité à 20)"""
        if hasattr(obj, 'status_history'):
            from .workflow_serializers import StatusHistorySerializer
            return StatusHistorySerializer(
                obj.status_history.all()[:20],
                many=True,
                context=self.context
            ).data
        return []


# ═══════════════════════════════════════════════════════════
# CREATE
# ═══════════════════════════════════════════════════════════

class OpportunityCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour création opportunité
    
    Usage:
        POST /opportunities/
    """
    
    client_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Opportunity
        fields = [
            'name',
            'client_id',
            'notes',
        ]
    
    def validate_name(self, value):
        """Valide et normalise nom"""
        return normalize_opportunity_name(value)
    
    def validate_client_id(self, value):
        """Valide que client existe"""
        from ...clients.models import Client
        
        try:
            Client.objects.get(id=value)
            return value
        except Client.DoesNotExist:
            raise serializers.ValidationError('Client introuvable')
    
    def validate(self, data):
        """Validation globale"""
        validate_opportunity_data(data)
        return data
    
    def create(self, validated_data):
        """
        NE PAS utiliser directement
        
        Utiliser le service: create_opportunity()
        """
        raise NotImplementedError(
            'Utiliser opportunities.services.create_opportunity() au lieu de serializer.save()'
        )


# ═══════════════════════════════════════════════════════════
# UPDATE
# ═══════════════════════════════════════════════════════════

class OpportunityUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour mise à jour opportunité
    
    Usage:
        PUT/PATCH /opportunities/{id}/
    """
    
    class Meta:
        model = Opportunity
        fields = [
            'name',
            'assigned_to',
            'notes',
        ]
    
    def validate(self, data):
        """Validation globale"""
        validate_opportunity_data(data, opportunity=self.instance)
        return data
    
    def update(self, instance, validated_data):
        """
        NE PAS utiliser directement
        
        Utiliser le service: update_opportunity()
        """
        raise NotImplementedError(
            'Utiliser opportunities.services.update_opportunity() au lieu de serializer.save()'
        )