"""
QUOTE SERIALIZERS

Transformation Quotes ↔ JSON:
- SupplierQuote + SupplierQuoteLine
- InsomeaQuote + InsomeaQuoteLine
"""

from rest_framework import serializers
from decimal import Decimal

from ..models import (
    SupplierQuote,
    SupplierQuoteLine,
    InsomeaQuote,
    InsomeaQuoteLine,
)
from ..validators import (
    validate_pdf_file,
    validate_file_size,
    validate_price_positive,
    validate_sale_price_greater_than_purchase,
    validate_insomea_quote_lines_pricing,
    validate_discount_percent,
)

# Import serializers from other apps
from ...suppliers.serializers import SupplierMinimalSerializer
from ...users.api.serializers import UserMinimalSerializer


# ═══════════════════════════════════════════════════════════
# SUPPLIER QUOTE
# ═══════════════════════════════════════════════════════════

class SupplierQuoteLineSerializer(serializers.ModelSerializer):
    """
    Serializer ligne devis fournisseur
    """
    
    opportunity_line = serializers.SerializerMethodField()
    
    class Meta:
        model = SupplierQuoteLine
        fields = [
            'id',
            'opportunity_line',
            'unit_price_purchase',
            'line_total_purchase',
            'currency',
            'delivery_time',
            'sku',
        ]
        read_only_fields = ['id', 'line_total_purchase']
    
    def get_opportunity_line(self, obj):
        """Retourne OpportunityLine minimal"""
        if obj.opportunity_line:
            from .line_serializers import OpportunityLineMinimalSerializer
            return OpportunityLineMinimalSerializer(
                obj.opportunity_line,
                context=self.context
            ).data
        return None


class SupplierQuoteSerializer(serializers.ModelSerializer):
    """
    Serializer devis fournisseur
    
    Usage:
        GET /supplier-quotes/
        GET /supplier-quotes/{id}/
    """
    
    supplier = SupplierMinimalSerializer(read_only=True)
    created_by = UserMinimalSerializer(read_only=True)
    
    # Lignes nested
    lines = SupplierQuoteLineSerializer(many=True, read_only=True)
    
    # Document URL
    document_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SupplierQuote
        fields = [
            'id',
            'supplier',
            'created_by',
            'reference',
            'document',
            'document_url',
            'received_at',
            
            # Totaux
            'subtotal_purchase',
            'discount_percent',
            'discount_amount',
            'total_purchase',
            
            # Lignes
            'lines',
            
            'created_at',
        ]
        read_only_fields = [
            'id',
            'subtotal_purchase',
            'discount_amount',
            'total_purchase',
            'created_at',
        ]
    
    def get_document_url(self, obj):
        """Retourne URL document (si existe)"""
        if obj.document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document.url)
            return obj.document.url
        return None


class CreateSupplierQuoteSerializer(serializers.Serializer):
    """
    Serializer pour création devis fournisseur
    
    Usage:
        POST /supplier-quotes/
    
    Input:
        {
            "supplier_id": "uuid",
            "reference": "REF-123",
            "document": <file>,
            "discount_percent": 5.00,
            "lines": [
                {
                    "line_id": "uuid",
                    "unit_price_purchase": 100.00,
                    "sku": "CFQ...",
                    "currency": "EUR",
                    "delivery_time": 7
                },
                ...
            ]
        }
    """
    
    supplier_id = serializers.UUIDField(write_only=True)
    
    reference = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )
    
    document = serializers.FileField(write_only=True)
    
    discount_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        required=False
    )
    
    lines = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )
    
    def validate_supplier_id(self, value):
        """Valide que supplier existe"""
        from ...suppliers.models import Supplier
        
        try:
            Supplier.objects.get(id=value)
            return value
        except Supplier.DoesNotExist:
            raise serializers.ValidationError('Fournisseur introuvable')
    
    def validate_document(self, value):
        """Valide PDF"""
        validate_pdf_file(value)
        validate_file_size(value, max_size_mb=10)
        return value
    
    def validate_discount_percent(self, value):
        """Valide discount"""
        validate_discount_percent(value)
        return value
    
    def validate_lines(self, value):
        """Valide lignes"""
        
        if not value:
            raise serializers.ValidationError('Au moins une ligne requise')
        
        # Valide chaque ligne
        for i, line_data in enumerate(value):
            # Fields requis
            required = ['line_id', 'unit_price_purchase']
            for field in required:
                if field not in line_data:
                    raise serializers.ValidationError({
                        f'lines[{i}]': f'{field} requis'
                    })
            
            # Valide prix
            try:
                price = Decimal(str(line_data['unit_price_purchase']))
                validate_price_positive(price)
            except Exception as e:
                raise serializers.ValidationError({
                    f'lines[{i}].unit_price_purchase': str(e)
                })
        
        return value
    
    def create(self, validated_data):
        """
        NE PAS utiliser directement
        
        Utiliser le service: create_supplier_quote()
        """
        raise NotImplementedError(
            'Utiliser opportunities.services.create_supplier_quote()'
        )


# ═══════════════════════════════════════════════════════════
# INSOMEA QUOTE
# ═══════════════════════════════════════════════════════════

class InsomeaQuoteLineSerializer(serializers.ModelSerializer):
    """
    Serializer ligne devis Insomea
    """
    
    opportunity_line = serializers.SerializerMethodField()
    supplier_quote_line = serializers.SerializerMethodField()
    
    # Calculs
    line_margin = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = InsomeaQuoteLine
        fields = [
            'id',
            'opportunity_line',
            'supplier_quote_line',
            
            # Prix achat (copié)
            'unit_price_purchase',
            'line_total_purchase',
            
            # Prix vente (commercial)
            'unit_price_sale',
            'line_total_sale',
            
            # Marge
            'line_margin',
            'line_discount',
        ]
        read_only_fields = [
            'id',
            'line_total_purchase',
            'line_total_sale',
            'line_margin',
        ]
    
    def get_opportunity_line(self, obj):
        """Retourne OpportunityLine minimal"""
        if obj.opportunity_line:
            from .line_serializers import OpportunityLineMinimalSerializer
            return OpportunityLineMinimalSerializer(
                obj.opportunity_line,
                context=self.context
            ).data
        return None
    
    def get_supplier_quote_line(self, obj):
        """Retourne SupplierQuoteLine source (référence)"""
        if obj.supplier_quote_line:
            return {
                'id': str(obj.supplier_quote_line.id),
                'unit_price_purchase': str(obj.supplier_quote_line.unit_price_purchase),
                'sku': obj.supplier_quote_line.sku,
            }
        return None


class InsomeaQuoteSerializer(serializers.ModelSerializer):
    """
    Serializer devis Insomea
    
    Usage:
        GET /insomea-quotes/
        GET /insomea-quotes/{id}/
    """
    
    opportunity = serializers.SerializerMethodField()
    created_by = UserMinimalSerializer(read_only=True)
    
    # Lignes nested
    lines = InsomeaQuoteLineSerializer(many=True, read_only=True)
    
    # Document URL
    document_url = serializers.SerializerMethodField()
    
    # Marge globale
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
    
    class Meta:
        model = InsomeaQuote
        fields = [
            'id',
            'opportunity',
            'created_by',
            'reference',
            'document',
            'document_url',
            
            # Totaux achat
            'subtotal_purchase',
            'total_purchase',
            
            # Totaux vente
            'subtotal_sale',
            'discount_percent',
            'discount_amount',
            'total_sale',
            
            # Marge
            'margin',
            'margin_percent',
            
            # Lignes
            'lines',
            
            'created_at',
        ]
        read_only_fields = [
            'id',
            'reference',
            'subtotal_purchase',
            'total_purchase',
            'subtotal_sale',
            'discount_amount',
            'total_sale',
            'margin',
            'margin_percent',
            'created_at',
        ]
    
    def get_opportunity(self, obj):
        """Retourne Opportunity minimal"""
        if obj.opportunity:
            from .opportunity_serializers import OpportunityMinimalSerializer
            return OpportunityMinimalSerializer(
                obj.opportunity,
                context=self.context
            ).data
        return None
    
    def get_document_url(self, obj):
        """Retourne URL document (si existe)"""
        if obj.document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document.url)
            return obj.document.url
        return None


class CreateInsomeaQuoteSerializer(serializers.Serializer):
    """
    Serializer pour création devis Insomea
    
    Usage:
        POST /opportunities/{id}/create-insomea-quote/
    
    Input:
        {
            "discount_percent": 10.00,
            "notes": "...",
            "lines_pricing": [
                {
                    "line_id": "uuid",
                    "supplier_quote_line_id": "uuid",  ← Choix commercial
                    "unit_price_sale": 120.00
                },
                ...
            ]
        }
    """
    
    discount_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        required=False
    )
    
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000
    )
    
    lines_pricing = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )
    
    def validate_discount_percent(self, value):
        """Valide discount"""
        validate_discount_percent(value)
        return value
    
    def validate_lines_pricing(self, value):
        """Valide pricing lignes"""
        
        if not value:
            raise serializers.ValidationError('Au moins une ligne requise')
        
        # Valide chaque ligne
        for i, line_data in enumerate(value):
            # Fields requis
            required = ['line_id', 'supplier_quote_line_id', 'unit_price_sale']
            for field in required:
                if field not in line_data:
                    raise serializers.ValidationError({
                        f'lines_pricing[{i}]': f'{field} requis'
                    })
            
            # Valide prix vente positif
            try:
                sale_price = Decimal(str(line_data['unit_price_sale']))
                validate_price_positive(sale_price)
            except Exception as e:
                raise serializers.ValidationError({
                    f'lines_pricing[{i}].unit_price_sale': str(e)
                })
        
        return value
    
    def validate(self, data):
        """Validation globale"""
        
        # Récupère SupplierQuoteLines pour vérifier prix achat
        lines_pricing = data['lines_pricing']
        
        from ..models import SupplierQuoteLine
        sql_ids = [lp['supplier_quote_line_id'] for lp in lines_pricing]
        sql_map = {
            str(sql.id): sql
            for sql in SupplierQuoteLine.objects.filter(id__in=sql_ids)
        }
        
        # Enrichit avec prix achat + validation
        for lp in lines_pricing:
            sql_id = str(lp['supplier_quote_line_id'])
            
            if sql_id not in sql_map:
                raise serializers.ValidationError({
                    'lines_pricing': f'SupplierQuoteLine {sql_id} introuvable'
                })
            
            sql = sql_map[sql_id]
            lp['unit_price_purchase'] = sql.unit_price_purchase
            
            # Valide sale >= purchase
            validate_sale_price_greater_than_purchase(
                lp['unit_price_purchase'],
                Decimal(str(lp['unit_price_sale']))
            )
        
        # Validation composite
        validate_insomea_quote_lines_pricing(lines_pricing)
        
        return data
    
    def create(self, validated_data):
        """
        NE PAS utiliser directement
        
        Utiliser le service: create_insomea_quote()
        """
        raise NotImplementedError(
            'Utiliser opportunities.services.create_insomea_quote()'
        )