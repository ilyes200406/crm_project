"""
OPPORTUNITY VIEWSET

Endpoints:
- GET    /opportunities/                 → list
- POST   /opportunities/                 → create
- GET    /opportunities/{id}/            → retrieve
- PUT    /opportunities/{id}/            → update
- PATCH  /opportunities/{id}/            → partial_update
- DELETE /opportunities/{id}/            → destroy (cancel)

Actions:
- POST   /opportunities/{id}/lines/                        → add_line
- POST   /opportunities/{id}/request-supplier-quotes/      → request_supplier_quotes
- POST   /opportunities/{id}/create-insomea-quote/         → create_insomea_quote
- POST   /opportunities/{id}/request-client-po/            → request_client_po
- POST   /opportunities/{id}/upload-client-po/             → upload_client_po
- POST   /opportunities/{id}/approve/                      → approve
- POST   /opportunities/{id}/create-insomea-pos/           → create_insomea_pos
- GET    /opportunities/stats/                             → stats
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from ..models import Opportunity
from ..serializers import (
    OpportunityListSerializer,
    OpportunityDetailSerializer,
    OpportunityCreateSerializer,
    OpportunityUpdateSerializer,
    OpportunityLineCreateSerializer,
    CreateInsomeaQuoteSerializer,
    UploadClientPOSerializer,
)
from ..selectors import (
    get_opportunities_queryset,
    get_opportunity_by_id,
    get_opportunity_stats,
)
from ..services import (
    create_opportunity,
    update_opportunity,
    delete_opportunity,
    add_line_to_opportunity,
    create_insomea_quote,
    upload_client_po,
    create_insomea_pos,
)
from ..services.workflow_service import (
    request_all_supplier_quotes,
    request_client_po,
    approve_opportunity,
)
from ..permissions import IsOpportunityOwnerOrAdmin
from ..filters import OpportunityFilter
from ...clients.models import Client
from ...products.models import Product
from ..serializers import OpportunityLineSerializer


class OpportunityViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OpportunityFilter
    search_fields = ['reference', 'name', 'client__company_name']
    ordering_fields = ['created_at', 'updated_at', 'reference']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        if self.action == 'retrieve':
            return get_opportunities_queryset(user=user, prefetch_lines=True, prefetch_quotes=True, prefetch_history=True)
        
        return get_opportunities_queryset(user=user)
    
    def get_serializer_class(self):

        if self.action == 'list':
            return OpportunityListSerializer
        elif self.action == 'retrieve':
            return OpportunityDetailSerializer
        elif self.action == 'create':
            return OpportunityCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OpportunityUpdateSerializer
        elif self.action == 'add_line':
            return OpportunityLineCreateSerializer
        elif self.action == 'create_insomea_quote':
            return CreateInsomeaQuoteSerializer
        elif self.action == 'upload_client_po':
            return UploadClientPOSerializer
        
        return OpportunityDetailSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOpportunityOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        client = Client.objects.get(id=serializer.validated_data['client_id'])
        
        opportunity = create_opportunity(
            data={
                'name': serializer.validated_data['name'],
                'client': client,
                'notes': serializer.validated_data.get('notes', ''),
            },
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        output_serializer = OpportunityDetailSerializer(opportunity, context={'request': request})        
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        
        opportunity = update_opportunity(
            opportunity_id=instance.id,
            data=serializer.validated_data,
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        output_serializer = OpportunityDetailSerializer(opportunity, context={'request': request})
        return Response(output_serializer.data)

    # Annule opportunité (soft delete)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        delete_opportunity(opportunity_id=instance.id, user=request.user, ip_address=self.get_client_ip(request))
        return Response({'detail': 'Opportunité annulée avec succès'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='lines')
    def add_line(self, request, pk=None):

        opportunity = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'opportunity': opportunity, 'request': request})
        serializer.is_valid(raise_exception=True)
        
        product = Product.objects.get(id=serializer.validated_data['product_id'])
        
        line = add_line_to_opportunity(
            opportunity_id=opportunity.id,
            data={
                'product': product,
                'quantity': serializer.validated_data['quantity'],
                'billing_cycle': serializer.validated_data.get('billing_cycle', 'ANNUAL'),
                'notes': serializer.validated_data.get('notes', ''),
            },
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        output_serializer = OpportunityLineSerializer(line, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='request-supplier-quotes')
    def request_supplier_quotes(self, request, pk=None):
        opportunity = self.get_object()
        opportunity = request_all_supplier_quotes(opportunity_id=opportunity.id, user=request.user, ip_address=self.get_client_ip(request))
        serializer = OpportunityDetailSerializer(opportunity, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='create-insomea-quote')
    def create_insomea_quote(self, request, pk=None):
        """
        POST /opportunities/{id}/create-insomea-quote/
        
        Crée devis Insomea pour le client
        
        Input:
            {
                "discount_percent": 10.00,
                "notes": "...",
                "lines_pricing": [
                    {
                        "line_id": "uuid",
                        "supplier_quote_line_id": "uuid",
                        "unit_price_sale": 120.00
                    },
                    ...
                ]
            }
        """
        opportunity = self.get_object()
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Utilise service
        insomea_quote = create_insomea_quote(
            opportunity_id=opportunity.id,
            lines_pricing=serializer.validated_data['lines_pricing'],
            discount_percent=serializer.validated_data.get('discount_percent', 0),
            notes=serializer.validated_data.get('notes', ''),
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Retourne devis créé
        from ..serializers import InsomeaQuoteSerializer
        output_serializer = InsomeaQuoteSerializer(
            insomea_quote,
            context={'request': request}
        )
        
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], url_path='request-client-po')
    def request_client_po(self, request, pk=None):
        """
        POST /opportunities/{id}/request-client-po/
        
        Marque devis Insomea comme envoyé au client
        
        Transition: INSOMEA_QUOTE_CREATED → CLIENT_PO_REQUEST
        """
        opportunity = self.get_object()
        
        # Utilise service
        opportunity = request_client_po(
            opportunity_id=opportunity.id,
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Retourne
        serializer = OpportunityDetailSerializer(
            opportunity,
            context={'request': request}
        )
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='upload-client-po')
    def upload_client_po(self, request, pk=None):
        """
        POST /opportunities/{id}/upload-client-po/
        
        Upload bon de commande client
        
        Input (multipart/form-data):
            {
                "po_number": "BC-CLIENT-001",
                "document": <file>
            }
        
        Transition: CLIENT_PO_REQUEST → CLIENT_PO_RECEIVED
        """
        opportunity = self.get_object()
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Utilise service
        client_po = upload_client_po(
            opportunity_id=opportunity.id,
            document=serializer.validated_data['document'],
            po_number=serializer.validated_data['po_number'],
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Retourne ClientPO créé
        from ..serializers import ClientPOSerializer
        output_serializer = ClientPOSerializer(
            client_po,
            context={'request': request}
        )
        
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        POST /opportunities/{id}/approve/
        
        Approuve opportunité (FINANCE)
        
        Crée provisions pour toutes lignes
        
        Transition: CLIENT_PO_RECEIVED → APPROVED
        """
        opportunity = self.get_object()
        
        # Utilise service
        result = approve_opportunity(
            opportunity_id=opportunity.id,
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Retourne opportunity + provisions créées
        opportunity_serializer = OpportunityDetailSerializer(
            result['opportunity'],
            context={'request': request}
        )
        
        from ..serializers import ProvisionSerializer
        provisions_serializer = ProvisionSerializer(
            result['provisions'],
            many=True,
            context={'request': request}
        )
        
        return Response({
            'opportunity': opportunity_serializer.data,
            'provisions': provisions_serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='create-insomea-pos')
    def create_insomea_pos(self, request, pk=None):
        """
        POST /opportunities/{id}/create-insomea-pos/
        
        Crée bons de commande Insomea vers fournisseurs
        
        Groupe lignes par fournisseur
        """
        opportunity = self.get_object()
        
        # Utilise service
        insomea_pos = create_insomea_pos(
            opportunity_id=opportunity.id,
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Retourne POs créés
        from ..serializers import InsomeaPOSerializer
        serializer = InsomeaPOSerializer(
            insomea_pos,
            many=True,
            context={'request': request}
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        GET /opportunities/stats/
        
        Statistiques opportunities (par statut)
        """
        stats = get_opportunity_stats(user=request.user)
        return Response(stats)
    
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