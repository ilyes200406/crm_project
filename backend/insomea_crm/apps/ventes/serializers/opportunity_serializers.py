"""
OPPORTUNITY SERIALIZERS - MODIFIÉ

Support renewal workflow
"""

from rest_framework import serializers
from django.db import transaction

from ..models import (
    Opportunity,
    OpportunityStatus,
    OpportunityType,  # 🆕 NOUVEAU
)
from ..validators import (
    validate_opportunity_name,
    validate_opportunity_editable,
)


# ═══════════════════════════════════════════════════════════
# OPPORTUNITY LIST SERIALIZER
# ═══════════════════════════════════════════════════════════

class OpportunityListSerializer(serializers.ModelSerializer):
    """
    Serializer liste Opportunités (léger)
    
    Usage:
        - GET /opportunities/
    """
    
    # Relations
    client_name = serializers.CharField(
        source='client.company_name',
        read_only=True
    )
    
    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name',
        read_only=True,
        allow_null=True
    )
    
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    
    # 🆕 NOUVEAU: Type
    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True
    )
    
    # 🆕 NOUVEAU: Parent opportunity (si renewal)
    parent_opportunity_reference = serializers.CharField(
        source='related_opportunity.reference',
        read_only=True,
        allow_null=True
    )
    
    # Status
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    # Computed
    lines_count = serializers.IntegerField(read_only=True)
    
    # 🆕 NOUVEAU: Flags
    is_renewal = serializers.BooleanField(read_only=True)
    is_initial = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Opportunity
        fields = [
            'id',
            'reference',
            'name',
            'type',  # 🆕 NOUVEAU
            'type_display',  # 🆕 NOUVEAU
            'client',
            'client_name',
            'status',
            'status_display',
            'assigned_to',
            'assigned_to_name',
            'created_by',
            'created_by_name',
            'related_opportunity',  # 🆕 NOUVEAU
            'parent_opportunity_reference',  # 🆕 NOUVEAU
            'lines_count',
            'is_renewal',  # 🆕 NOUVEAU
            'is_initial',  # 🆕 NOUVEAU
            'created_at',
            'updated_at',
        ]


# ═══════════════════════════════════════════════════════════
# OPPORTUNITY DETAIL SERIALIZER
# ═══════════════════════════════════════════════════════════

class OpportunityDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détail Opportunité (complet)
    
    Usage:
        - GET /opportunities/:id/
    """
    
    # Relations (nested)
    client = serializers.SerializerMethodField()
    assigned_to = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    
    # 🆕 NOUVEAU: Type
    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True
    )
    
    # 🆕 NOUVEAU: Related opportunities
    related_opportunity = serializers.SerializerMethodField()
    child_opportunities = serializers.SerializerMethodField()
    
    # Lines (nested)
    lines = serializers.SerializerMethodField()
    
    # Quotes
    supplier_quotes = serializers.SerializerMethodField()
    insomea_quote = serializers.SerializerMethodField()
    
    # PO
    client_po = serializers.SerializerMethodField()
    insomea_pos = serializers.SerializerMethodField()
    
    # Status
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    # Computed
    lines_count = serializers.IntegerField(read_only=True)
    total_amount_estimate = serializers.SerializerMethodField()
    
    # 🆕 NOUVEAU: Flags
    is_renewal = serializers.BooleanField(read_only=True)
    is_initial = serializers.BooleanField(read_only=True)
    
    # Permissions
    can_edit = serializers.SerializerMethodField()
    can_add_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Opportunity
        fields = [
            'id',
            'reference',
            'name',
            'type',  # 🆕 NOUVEAU
            'type_display',  # 🆕 NOUVEAU
            'client',
            'status',
            'status_display',
            'assigned_to',
            'created_by',
            'related_opportunity',  # 🆕 NOUVEAU
            'child_opportunities',  # 🆕 NOUVEAU
            'notes',
            'cancellation_reason',
            'lines',
            'lines_count',
            'supplier_quotes',
            'insomea_quote',
            'client_po',
            'insomea_pos',
            'total_amount_estimate',
            'is_renewal',  # 🆕 NOUVEAU
            'is_initial',  # 🆕 NOUVEAU
            'can_edit',
            'can_add_items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'reference',
            'status',
            'created_at',
            'updated_at',
        ]
    
    def get_client(self, obj):
        """Client info"""
        from ...clients.serializers import ClientListSerializer
        return ClientListSerializer(obj.client).data
    
    def get_assigned_to(self, obj):
        """Assigned to user"""
        if obj.assigned_to:
            from ...users.api.serializers import UserSerializer
            return UserSerializer(obj.assigned_to).data
        return None
    
    def get_created_by(self, obj):
        """Created by user"""
        from ...users.api.serializers import UserSerializer
        return UserSerializer(obj.created_by).data
    
    # 🆕 NOUVEAU
    def get_related_opportunity(self, obj):
        """Parent opportunity (si renewal)"""
        if obj.related_opportunity:
            return OpportunityListSerializer(obj.related_opportunity).data
        return None
    
    # 🆕 NOUVEAU
    def get_child_opportunities(self, obj):
        """Child opportunities (renewals, upsells)"""
        children = obj.get_child_opportunities()
        return OpportunityListSerializer(children, many=True).data
    
    def get_lines(self, obj):
        """OpportunityLines"""
        from .line_serializers import OpportunityLineListSerializer
        lines = obj.lines.all().order_by('created_at')
        return OpportunityLineListSerializer(lines, many=True).data

    # ═══════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════
    def _get_related(self, obj, field_name):
        try:
            return getattr(obj, field_name)
        except Exception as e:
            return None
    def _serialize_related(self, obj, field_name, serializer_class, many=False):
        related = self._get_related(obj, field_name)
        if not related:
            return None if not many else []
        return serializer_class(related, many=many).data
    
    
    def get_supplier_quotes(self, obj):
        from .quote_serializers import SupplierQuoteListSerializer
        quotes = (
            obj.lines
            .filter(supplier_quote_line__isnull=False)
            .select_related('supplier_quote_line__supplier_quote')
            .values_list('supplier_quote_line__supplier_quote', flat=True)
            .distinct()
        )
        from ..models import SupplierQuote
        queryset = SupplierQuote.objects.filter(id__in=quotes)
        return SupplierQuoteListSerializer(queryset, many=True).data
    
    def get_insomea_quote(self, obj):
        """InsomeaQuote"""
        from .quote_serializers import InsomeaQuoteDetailSerializer
        return self._serialize_related(obj, 'insomea_quote', InsomeaQuoteDetailSerializer)
    
    def get_client_po(self, obj):
        """Client PO"""
        from .workflow_serializers import ClientPOSerializer
        return self._serialize_related(obj, 'client_purchase_order', ClientPOSerializer)
    
    def get_insomea_pos(self, obj):
        """Insomea POs"""
        from .workflow_serializers import InsomeaPurchaseOrderListSerializer
        from ..models import InsomeaPurchaseOrder

        po_ids = (
            obj.lines.exclude(insomea_purchase_order__isnull=True)
            .values_list('insomea_purchase_order_id', flat=True)
            .distinct()
        )
        pos = InsomeaPurchaseOrder.objects.filter(id__in=po_ids)
        return InsomeaPurchaseOrderListSerializer(pos, many=True).data
    
    def get_total_amount_estimate(self, obj):
        """Total estimated (from InsomeaQuote if exists)"""
        quote = self._get_related(obj, 'insomea_quote')
        return quote.total_sale if quote else None
    
    def get_can_edit(self, obj):
        """Check if user can edit"""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        return obj.can_edit()
    
    def get_can_add_items(self, obj):
        """Check if can add items"""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        return obj.can_add_items()


# ═══════════════════════════════════════════════════════════
# OPPORTUNITY CREATE/UPDATE SERIALIZERS
# ═══════════════════════════════════════════════════════════

class OpportunityCreateSerializer(serializers.ModelSerializer):
    """
    Serializer création Opportunité
    
    Usage:
        - POST /opportunities/
    
    🆕 MODIFIÉ: Support type + related_opportunity
    """
    
    class Meta:
        model = Opportunity
        fields = [
            'name',
            'client',
            'type',  # 🆕 NOUVEAU
            'related_opportunity',  # 🆕 NOUVEAU
            'assigned_to',
            'notes',
        ]
    
    def validate_name(self, value):
        """Validate name"""
        validate_opportunity_name(value)
        return value
    
    def validate(self, attrs):
        """Validation"""
        
        # 🆕 NOUVEAU: Si RENEWAL, related_opportunity requis
        if attrs.get('type') == OpportunityType.RENEWAL:
            if not attrs.get('related_opportunity'):
                raise serializers.ValidationError({
                    'related_opportunity': 'Required for RENEWAL type'
                })
        
        # 🆕 NOUVEAU: Si type != RENEWAL, related_opportunity pas permis
        if attrs.get('type') != OpportunityType.RENEWAL:
            if attrs.get('related_opportunity'):
                raise serializers.ValidationError({
                    'related_opportunity': 'Only allowed for RENEWAL type'
                })
        
        return attrs


class OpportunityUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer update Opportunité
    
    Usage:
        - PATCH /opportunities/:id/
    
    Note:
        Type et related_opportunity non modifiables après création
    """
    
    class Meta:
        model = Opportunity
        fields = [
            'name',
            'assigned_to',
            'notes',
        ]
    
    def validate(self, attrs):
        """Validation"""
        opportunity = self.instance
        
        # Check if editable
        validate_opportunity_editable(opportunity)
        
        return attrs


# ═══════════════════════════════════════════════════════════
# WORKFLOW SERIALIZERS
# ═══════════════════════════════════════════════════════════

class RequestSupplierQuotesSerializer(serializers.Serializer):
    """
    Serializer request supplier quotes
    
    Usage:
        POST /opportunities/:id/request_supplier_quotes/
    
    Input: (vide)
    """
    pass


class RequestClientPOSerializer(serializers.Serializer):
    """
    Serializer request client PO
    
    Usage:
        POST /opportunities/:id/request_client_po/
    
    Input: (vide)
    """
    pass


class ApproveOpportunitySerializer(serializers.Serializer):
    """
    Serializer approve opportunity
    
    Usage:
        POST /opportunities/:id/approve/
    
    Input: (vide)
    """
    pass


class CancelOpportunitySerializer(serializers.Serializer):
    """
    Serializer cancel opportunity
    
    Usage:
        POST /opportunities/:id/cancel/
    """
    
    reason = serializers.CharField(
        required=True,
        help_text="Raison annulation"
    )


class OpportunityMinimalSerializer(serializers.ModelSerializer):
    """Serializer minimal pour nested quote payloads."""

    class Meta:
        model = Opportunity
        fields = ['id', 'reference', 'name', 'status', 'type']
