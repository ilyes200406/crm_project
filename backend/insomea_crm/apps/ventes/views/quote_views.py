"""
QUOTE VIEWSETS

SupplierQuoteViewSet:
- GET    /supplier-quotes/              → list
- POST   /supplier-quotes/              → create
- GET    /supplier-quotes/{id}/         → retrieve

InsomeaQuoteViewSet:
- GET    /insomea-quotes/               → list
- GET    /insomea-quotes/{id}/          → retrieve
- GET    /insomea-quotes/{id}/download/ → download PDF
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.http import FileResponse

from ..models import SupplierQuote, InsomeaQuote
from ..serializers import (
    SupplierQuoteSerializer,
    CreateSupplierQuoteSerializer,
    InsomeaQuoteSerializer,
)
from ..services import create_supplier_quote
from ..permissions import CanCreateSupplierQuote
from ..filters import SupplierQuoteFilter, InsomeaQuoteFilter


# ═══════════════════════════════════════════════════════════
# SUPPLIER QUOTE VIEWSET
# ═══════════════════════════════════════════════════════════

class SupplierQuoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour SupplierQuote (devis fournisseur)
    
    CRUD (read-only après création)
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SupplierQuoteFilter
    search_fields = ['reference', 'supplier__name']
    ordering_fields = ['recieved_at']
    ordering = ['-recieved_at']
    
    # READ-ONLY après création (pas de update/delete)
    http_method_names = ['get', 'post', 'head', 'options']
    
    def get_queryset(self):
        """
        Queryset avec RBAC + optimisation
        """
        user = self.request.user
        
        queryset = SupplierQuote.objects.select_related(
            'supplier',
            'created_by',
        ).prefetch_related(
            'lines',
            'lines__opportunity_line',
            'lines__opportunity_line__product',
            'lines__opportunity_line__opportunity',
        )
        
        # RBAC filtering
        if user.role == 'COMMERCIAL':
            # Voit devis pour ses opportunités
            queryset = queryset.filter(
                lines__opportunity_line__opportunity__created_by=user
            ) | queryset.filter(
                lines__opportunity_line__opportunity__assigned_to=user
            )
        
        elif user.role == 'TECHNICIEN':
            # Voit devis opportunités APPROVED
            from ..models import OpportunityStatus
            queryset = queryset.filter(
                lines__opportunity_line__opportunity__status=OpportunityStatus.APPROUVED
            )
        
        elif user.role == 'FINANCE':
            # Voit tous devis opportunités en phase avancée
            from ..models import OpportunityStatus
            queryset = queryset.filter(
                lines__opportunity_line__opportunity__status__in=[
                    OpportunityStatus.CLIENT_PO_RECIEVED,
                    OpportunityStatus.APPROUVED,
                ]
            )
        
        # ADMIN: voit tout
        
        return queryset.distinct()
    
    def get_serializer_class(self):
        """
        Serializer selon action
        """
        if self.action == 'create':
            return CreateSupplierQuoteSerializer
        return SupplierQuoteSerializer
    
    def get_permissions(self):
        """
        Permissions selon action
        """
        if self.action == 'create':
            return [CanCreateSupplierQuote()]
        return [IsAuthenticated()]
    
    # ═══════════════════════════════════════════════════════
    # CREATE
    # ═══════════════════════════════════════════════════════
    
    def create(self, request, *args, **kwargs):
        """
        POST /supplier-quotes/
        
        Upload devis fournisseur + créé lignes
        
        Input (multipart/form-data):
            {
                "supplier_id": "uuid",
                "reference": "REF-FOURNISSEUR-123",
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
        serializer = self.get_serializer(data=request.data)

        # serializer.is_valid(raise_exception=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        # Utilise service
        supplier_quote = create_supplier_quote(
            supplier_id=serializer.validated_data['supplier_id'],
            document=serializer.validated_data['document'],
            lines_data=serializer.validated_data['lines'],
            reference=serializer.validated_data.get('reference', ''),
            discount_percent=serializer.validated_data.get('discount_percent', 0),
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Retourne
        output_serializer = SupplierQuoteSerializer(
            supplier_quote,
            context={'request': request}
        )
        
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    # ═══════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════
    
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """
        GET /supplier-quotes/{id}/download/
        
        Télécharge PDF devis fournisseur
        """
        supplier_quote = self.get_object()
        
        if not supplier_quote.document:
            return Response(
                {'detail': 'Aucun document disponible'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Retourne fichier
        response = FileResponse(
            supplier_quote.document.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{supplier_quote.reference or supplier_quote.id}.pdf"'
        
        return response
    
    # ═══════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════
    
    def get_client_ip(self, request):
        """Récupère IP client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# ═══════════════════════════════════════════════════════════
# INSOMEA QUOTE VIEWSET
# ═══════════════════════════════════════════════════════════

class InsomeaQuoteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour InsomeaQuote (devis Insomea)
    
    READ-ONLY (création via OpportunityViewSet.create_insomea_quote)
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = InsomeaQuoteFilter
    search_fields = ['reference', 'opportunity__reference', 'opportunity__name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    serializer_class = InsomeaQuoteSerializer
    
    def get_queryset(self):
        """
        Queryset avec RBAC + optimisation
        """
        user = self.request.user
        
        queryset = InsomeaQuote.objects.select_related(
            'opportunity',
            'opportunity__client',
            'created_by',
        ).prefetch_related(
            'lines',
            'lines__opportunity_line',
            'lines__opportunity_line__product',
            'lines__supplier_quote_line',
            'lines__supplier_quote_line__supplier_quote',
        )
        
        # RBAC filtering
        if user.role == 'COMMERCIAL':
            queryset = queryset.filter(
                opportunity__created_by=user
            ) | queryset.filter(
                opportunity__assigned_to=user
            )
        
        elif user.role == 'TECHNICIEN':
            # Voit devis opportunités APPROVED
            from ..models import OpportunityStatus
            queryset = queryset.filter(
                opportunity__status=OpportunityStatus.APPROUVED
            )
        
        elif user.role == 'FINANCE':
            # Voit tous devis en phase avancée
            from ..models import OpportunityStatus
            queryset = queryset.filter(
                opportunity__status__in=[
                    OpportunityStatus.CLIENT_PO_REQUEST,
                    OpportunityStatus.CLIENT_PO_RECIEVED,
                    OpportunityStatus.APPROUVED,
                ]
            )
        
        # ADMIN: voit tout
        
        return queryset.distinct()
    
    # ═══════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════
    
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """
        GET /insomea-quotes/{id}/download/
        
        Télécharge PDF devis Insomea
        
        Note:
            Si document pas encore généré, retourne 404
            (génération PDF à implémenter dans service)
        """
        insomea_quote = self.get_object()
        
        if not insomea_quote.document:
            return Response(
                {'detail': 'Document en cours de génération. Réessayez dans quelques instants.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Retourne fichier
        response = FileResponse(
            insomea_quote.document.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{insomea_quote.reference}.pdf"'
        
        return response
    
    @action(detail=True, methods=['get'], url_path='preview')
    def preview(self, request, pk=None):
        """
        GET /insomea-quotes/{id}/preview/
        
        Retourne données pour preview devis (sans générer PDF)
        
        Frontend peut utiliser ces données pour afficher preview HTML
        """
        insomea_quote = self.get_object()
        
        # Serializer complet déjà inclut toutes données
        serializer = self.get_serializer(insomea_quote)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='by-opportunity/(?P<opportunity_id>[^/.]+)')
    def by_opportunity(self, request, opportunity_id=None):
        """
        GET /insomea-quotes/by-opportunity/{opportunity_id}/
        
        Récupère devis Insomea pour une opportunité
        
        Returns: InsomeaQuote ou 404
        """
        from ..models import Opportunity
        
        try:
            opportunity = Opportunity.objects.get(id=opportunity_id)
        except Opportunity.DoesNotExist:
            return Response(
                {'detail': 'Opportunité introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifie permissions
        if request.user.role == 'COMMERCIAL':
            if opportunity.created_by != request.user and opportunity.assigned_to != request.user:
                return Response(
                    {'detail': 'Action non autorisée'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Récupère InsomeaQuote
        try:
            insomea_quote = InsomeaQuote.objects.get(opportunity=opportunity)
        except InsomeaQuote.DoesNotExist:
            return Response(
                {'detail': 'Aucun devis Insomea pour cette opportunité'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Retourne
        serializer = self.get_serializer(insomea_quote)
        return Response(serializer.data)
