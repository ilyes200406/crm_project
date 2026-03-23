"""
WORKFLOW SERIALIZERS

Serializers pour:
- ClientPO
- InsomeaPurchaseOrder
- StatusHistory
"""

from rest_framework import serializers

from ..models import ClientPO, InsomeaPurchaseOrder, StatusHistory
from ..validators import validate_pdf_file, validate_file_size

# Import serializers
from ...suppliers.serializers import SupplierMinimalSerializer
from ...users.api.serializers import UserMinimalSerializer


# ═══════════════════════════════════════════════════════════
# CLIENT PO
# ═══════════════════════════════════════════════════════════

class ClientPOSerializer(serializers.ModelSerializer):
    """
    Serializer ClientPO (bon de commande client)
    
    Usage:
        GET (nested dans OpportunityDetailSerializer)
    """
    
    created_by = UserMinimalSerializer(read_only=True)
    document_url = serializers.SerializerMethodField()
    received_at = serializers.DateTimeField(source='recieved_at', read_only=True)
    created_at = serializers.DateTimeField(source='recieved_at', read_only=True)
    
    class Meta:
        model = ClientPO
        fields = [
            'id',
            'po_number',
            'document',
            'document_url',
            'received_at',
            'created_by',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_document_url(self, obj):
        """Retourne URL document"""
        if obj.document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document.url)
            return obj.document.url
        return None


class UploadClientPOSerializer(serializers.Serializer):
    """
    Serializer action: Upload BC client
    
    Usage:
        POST /opportunities/{id}/upload-client-po/
    
    Input:
        {
            "po_number": "BC-CLIENT-2024-001",
            "document": <file>
        }
    """
    
    po_number = serializers.CharField(max_length=100)
    document = serializers.FileField()
    
    def validate_document(self, value):
        """Valide PDF"""
        validate_pdf_file(value)
        validate_file_size(value, max_size_mb=10)
        return value


# ═══════════════════════════════════════════════════════════
# INSOMEA PO
# ═══════════════════════════════════════════════════════════

class InsomeaPOSerializer(serializers.ModelSerializer):
    """
    Serializer InsomeaPurchaseOrder (BC Insomea vers fournisseur)
    
    Usage:
        GET /insomea-pos/
        GET (nested dans OpportunityLine)
    """
    
    supplier = SupplierMinimalSerializer(read_only=True)
    created_by = UserMinimalSerializer(read_only=True)
    document_url = serializers.SerializerMethodField()
    
    # Lignes liées (via reverse FK)
    lines_count = serializers.SerializerMethodField()
    
    class Meta:
        model = InsomeaPurchaseOrder
        fields = [
            'id',
            'supplier',
            'po_number',
            'document',
            'document_url',
            'lines_count',
            'created_by',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_document_url(self, obj):
        """Retourne URL document"""
        if obj.document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document.url)
            return obj.document.url
        return None
    
    def get_lines_count(self, obj):
        """Nombre de lignes liées à ce PO"""
        return obj.opportunity_lines.count()


class InsomeaPurchaseOrderListSerializer(InsomeaPOSerializer):
    """Alias pour cohérence avec les serializers d'opportunity."""
    pass


# ═══════════════════════════════════════════════════════════
# STATUS HISTORY
# ═══════════════════════════════════════════════════════════

class StatusHistorySerializer(serializers.ModelSerializer):
    """
    Serializer StatusHistory (audit trail)
    
    Usage:
        GET (nested dans OpportunityDetailSerializer)
        GET /status-history/
    """
    
    changed_by = UserMinimalSerializer(read_only=True)
    entity_type = serializers.CharField(source='get_entity_type', read_only=True)
    entity = serializers.SerializerMethodField()
    
    class Meta:
        model = StatusHistory
        fields = [
            'id',
            'entity_type',
            'entity',
            'status_precedent',
            'status_suivant',
            'transition_name',
            'description',
            'metadata',
            'changed_by',
            'ip_address',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_entity(self, obj):
        """Retourne référence entité concernée"""
        entity = obj.get_entity()
        
        if not entity:
            return None
        
        # Retourne infos minimales selon type
        if obj.opportunity_line:
            return {
                'id': str(obj.opportunity_line.id),
                'product': obj.opportunity_line.product.title if obj.opportunity_line.product else None,
            }
        elif obj.opportunity:
            return {
                'id': str(obj.opportunity.id),
                'reference': obj.opportunity.reference,
                'name': obj.opportunity.name,
            }
        elif obj.provision:
            return {
                'id': str(obj.provision.id),
                'opportunity_line_id': str(obj.provision.opportunity_line_id),
            }
        
        return None
