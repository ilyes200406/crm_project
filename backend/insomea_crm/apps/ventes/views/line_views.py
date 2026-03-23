"""
OPPORTUNITY LINE VIEWSET

Endpoints:
- GET    /opportunity-lines/              → list
- POST   /opportunity-lines/              → create
- GET    /opportunity-lines/{id}/         → retrieve
- PUT    /opportunity-lines/{id}/         → update
- PATCH  /opportunity-lines/{id}/         → partial_update
- DELETE /opportunity-lines/{id}/         → destroy

Actions:
- POST   /opportunity-lines/{id}/request-supplier-quote/   → request_supplier_quote
- POST   /opportunity-lines/{id}/cancel/                   → cancel
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from ..models import OpportunityLine
from ..serializers import (
    OpportunityLineSerializer,
    OpportunityLineCreateSerializer,
    OpportunityLineUpdateSerializer,
)
from ..selectors import get_line_by_id
from ..services import (
    add_line_to_opportunity,
    update_opportunity_line,
    remove_line_from_opportunity,
)
from ..permissions import IsOpportunityOwnerOrAdmin
from ..filters import OpportunityLineFilter
from ..models import Opportunity
from ...products.models import Product
from ..models import OpportunityStatus


class OpportunityLineViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OpportunityLineFilter
    search_fields = ['product__title', 'notes']
    ordering_fields = ['created_at', 'quantity']
    ordering = ['created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        queryset = OpportunityLine.objects.select_related(
            'product',
            'opportunity',
            'opportunity__client',
            'opportunity__created_by',
            'insomea_purchase_order',
        ).prefetch_related(
            'supplier_quote_line',
            'insomea_quote_line',
            'provision',
        )
        
        # RBAC filtering
        if user.role == 'COMMERCIAL':
            queryset = queryset.filter(
                opportunity__created_by=user
            ) | queryset.filter(
                opportunity__assigned_to=user
            )
        
        elif user.role == 'TECHNICIEN':
            queryset = queryset.filter(
                opportunity__status=OpportunityStatus.APPROUVED
            ) | queryset.filter(
                opportunity__assigned_to=user
            )
        
        elif user.role == 'FINANCE':
            queryset = queryset.filter(
                opportunity__status__in=[
                    OpportunityStatus.CLIENT_PO_RECIEVED,
                    OpportunityStatus.APPROUVED,
                ]
            ) | queryset.filter(
                opportunity__assigned_to=user
            )
        
        # ADMIN: voit tout
        
        return queryset.distinct()
    
    def get_serializer_class(self):
        """
        Serializer selon action
        """
        if self.action == 'create':
            return OpportunityLineCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OpportunityLineUpdateSerializer
        return OpportunityLineSerializer
    
    def get_permissions(self):
        """
        Permissions selon action
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOpportunityOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    # ═══════════════════════════════════════════════════════
    # CRUD OVERRIDES
    # ═══════════════════════════════════════════════════════
    
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        opportunity = serializer.validated_data['opportunity']
        product = serializer.validated_data['product']
        
        # Vérifie permissions sur opportunity
        if request.user.role == 'COMMERCIAL':
            if opportunity.created_by != request.user and opportunity.assigned_to != request.user:
                return Response(
                    {'detail': 'Action non autorisée'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Utilise service
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
        
        # Retourne
        output_serializer = OpportunityLineSerializer(
            line,
            context={'request': request}
        )
        
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """
        PUT/PATCH /opportunity-lines/{id}/
        
        Met à jour ligne
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        
        # Utilise service
        line = update_opportunity_line(
            line_id=instance.id,
            data=serializer.validated_data,
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Retourne
        output_serializer = OpportunityLineSerializer(
            line,
            context={'request': request}
        )
        
        return Response(output_serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        DELETE /opportunity-lines/{id}/
        
        Supprime ligne
        """
        instance = self.get_object()
        
        # Utilise service
        remove_line_from_opportunity(
            line_id=instance.id,
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        return Response(
            {'detail': 'Ligne supprimée avec succès'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    # ═══════════════════════════════════════════════════════
    # ACTIONS FSM
    # ═══════════════════════════════════════════════════════
    
    @action(detail=True, methods=['post'], url_path='request-supplier-quote')
    def request_supplier_quote(self, request, pk=None):
        """
        POST /opportunity-lines/{id}/request-supplier-quote/
        
        Transition FSM: DRAFT → SUPPLIER_QUOTE_REQUEST
        
        Note:
            Généralement appelé via batch sur toutes lignes
            (OpportunityViewSet.request_supplier_quotes)
        """
        line = self.get_object()
        
        # FSM transition
        from ..models import OpportunityLineStatus
        
        if line.status != OpportunityLineStatus.DRAFT:
            return Response(
                {'detail': 'La ligne doit être en brouillon'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        line.request_supplier_quote()
        line.save()
        # Signal FSM → StatusHistory créé auto
        # Signal post_save → update_opportunity_status_from_lines()
        
        # Retourne
        serializer = OpportunityLineSerializer(
            line,
            context={'request': request}
        )
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        POST /opportunity-lines/{id}/cancel/
        
        Annule ligne (FSM transition → CANCELLED)
        
        Input (optionnel):
            {
                "reason": "Produit non disponible"
            }
        """
        line = self.get_object()
        
        # FSM transition
        from ..models import OpportunityLineStatus
        
        if line.status == OpportunityLineStatus.CANCELLED:
            return Response(
                {'detail': 'La ligne est déjà annulée'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', 'Annulation manuelle')
        
        line.cancel(reason=reason)
        line.save()
        # Signal FSM → StatusHistory créé auto
        # Signal post_save → update_opportunity_status_from_lines()
        
        # Retourne
        serializer = OpportunityLineSerializer(
            line,
            context={'request': request}
        )
        
        return Response(serializer.data)
    
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
