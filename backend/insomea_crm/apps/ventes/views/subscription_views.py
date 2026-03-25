"""
SUBSCRIPTION VIEWS

ViewSet pour Subscriptions
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from ..models import Subscription, SubscriptionStatus
from ..serializers import (
    SubscriptionListSerializer,
    SubscriptionDetailSerializer,
    SubscriptionUpdateSerializer,
    CreateRenewalSerializer,
    RenewalDataSerializer,
)
from ..selectors import (
    get_all_subscriptions,
    get_subscription_by_id,
    get_active_subscriptions,
    get_pending_renewal_subscriptions,
    get_expiring_subscriptions,
    get_subscription_stats,
)
from ..services import (
    create_renewal_opportunity,
    prepare_renewal_data_from_subscription,
    cancel_subscription,
)
from ..filters import SubscriptionFilter


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet Subscriptions
    
    Endpoints:
        GET    /subscriptions/                 - Liste
        GET    /subscriptions/:id/             - Détail
        PATCH  /subscriptions/:id/             - Update (auto_renew only)
        
        GET    /subscriptions/active/          - Actives
        GET    /subscriptions/expiring/        - Expirant bientôt
        GET    /subscriptions/pending_renewal/ - Pending renewal
        GET    /subscriptions/stats/           - Stats globales
        
        POST   /subscriptions/:id/create_renewal/  - Créer renewal
        GET    /subscriptions/:id/renewal_data/    - Data pré-remplies
        POST   /subscriptions/:id/cancel/          - Annuler
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SubscriptionFilter
    search_fields = ['subscription_number', 'client__company_name', 'product__title']
    ordering_fields = ['created_at', 'current_term_end', 'subscription_number']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get queryset"""
        return get_all_subscriptions(user=self.request.user)
    
    def get_serializer_class(self):
        """Get serializer class"""
        if self.action == 'list':
            return SubscriptionListSerializer
        elif self.action in ['update', 'partial_update']:
            return SubscriptionUpdateSerializer
        elif self.action == 'create_renewal':
            return CreateRenewalSerializer
        elif self.action == 'renewal_data':
            return RenewalDataSerializer
        else:
            return SubscriptionDetailSerializer
    
    def get_object(self):
        """Get object"""
        subscription_id = self.kwargs.get('pk')
        return get_subscription_by_id(
            subscription_id,
            user=self.request.user
        )
    
    # ───────────────────────────────────────────────────────
    # CRUD ACTIONS
    # ───────────────────────────────────────────────────────
    
    def list(self, request):
        """
        Liste subscriptions
        
        Query params:
            - status: ACTIVE, PENDING_RENEWAL, EXPIRED, CANCELLED
            - client: UUID
            - product: UUID
            - expiring: bool (si true, filtre expiring 30j)
        """
        
        queryset = self.filter_queryset(self.get_queryset())
        
        # Filtre expiring (custom)
        if request.query_params.get('expiring') == 'true':
            queryset = get_expiring_subscriptions(days=30, user=request.user)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Détail subscription"""
        subscription = self.get_object()
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    def partial_update(self, request, pk=None):
        """
        Update subscription (auto_renew seulement)
        
        Body:
            {
                "auto_renew": true/false
            }
        """
        
        subscription = self.get_object()
        serializer = self.get_serializer(
            subscription,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return détail
        output = SubscriptionDetailSerializer(subscription)
        return Response(output.data)
    
    # ───────────────────────────────────────────────────────
    # CUSTOM ACTIONS - LISTS
    # ───────────────────────────────────────────────────────
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Liste subscriptions actives
        
        GET /subscriptions/active/
        """
        
        queryset = get_active_subscriptions(user=request.user)
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SubscriptionListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring(self, request):
        """
        Liste subscriptions expirant bientôt
        
        GET /subscriptions/expiring/?days=30
        
        Query params:
            - days: int (default 30)
        """
        
        days = int(request.query_params.get('days', 30))
        queryset = get_expiring_subscriptions(days=days, user=request.user)
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SubscriptionListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_renewal(self, request):
        """
        Liste subscriptions pending renewal
        
        GET /subscriptions/pending_renewal/
        """
        
        queryset = get_pending_renewal_subscriptions(user=request.user)
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SubscriptionListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Stats globales subscriptions
        
        GET /subscriptions/stats/
        
        Returns:
            {
                "total": 150,
                "active": 120,
                "pending_renewal": 20,
                "expired": 10,
                "expiring_30d": 15,
                "expiring_7d": 5
            }
        """
        
        stats = get_subscription_stats(user=request.user)
        return Response(stats)
    
    # ───────────────────────────────────────────────────────
    # CUSTOM ACTIONS - RENEWAL
    # ───────────────────────────────────────────────────────
    
    @action(detail=True, methods=['post'])
    def create_renewal(self, request, pk=None):
        """
        Créer opportunité renewal
        
        POST /subscriptions/:id/create_renewal/
        
        Body (optionnel):
            {
                "quantity": 15,  // Modifier quantité (optionnel)
                "notes": "Notes"
            }
        
        Returns:
            {
                "opportunity": {...},
                "line": {...}
            }
        """
        
        subscription = self.get_object()
        
        # Validate input
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create renewal
        result = create_renewal_opportunity(
            subscription=subscription,
            user=request.user,
            quantity=serializer.validated_data.get('quantity'),
            notes=serializer.validated_data.get('notes', ''),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Return
        from ..serializers import OpportunityDetailSerializer, OpportunityLineDetailSerializer
        
        return Response({
            'opportunity': OpportunityDetailSerializer(result['opportunity']).data,
            'line': OpportunityLineDetailSerializer(result['line']).data,
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def renewal_data(self, request, pk=None):
        """
        Données pré-remplies pour renewal
        
        GET /subscriptions/:id/renewal_data/
        
        Returns:
            {
                "subscription_id": "...",
                "client_name": "...",
                "product_name": "...",
                "quantity": 10,
                "last_unit_price_sale": 150.00,
                ...
            }
        """
        
        subscription = self.get_object()
        
        # Prepare data
        data = prepare_renewal_data_from_subscription(subscription)
        
        # Serialize
        serializer = self.get_serializer(data)
        return Response(serializer.data)
    
    # ───────────────────────────────────────────────────────
    # CUSTOM ACTIONS - STATUS
    # ───────────────────────────────────────────────────────
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Annuler subscription
        
        POST /subscriptions/:id/cancel/
        
        Body:
            {
                "reason": "Raison annulation"
            }
        
        Note:
            Seulement si EXPIRED
        """
        
        subscription = self.get_object()
        
        # Validate status
        if subscription.status != SubscriptionStatus.EXPIRED:
            return Response({
                'error': 'Subscription must be EXPIRED to cancel'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get reason
        reason = request.data.get('reason', '')
        
        # Cancel
        cancel_subscription(
            subscription=subscription,
            reason=reason,
            user=request.user
        )
        
        # Return
        serializer = SubscriptionDetailSerializer(subscription)
        return Response(serializer.data)
