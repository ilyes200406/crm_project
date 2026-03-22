"""
PROVISION & SUBSCRIPTION VIEWSETS

ProvisionViewSet:
- GET    /provisions/              → list
- GET    /provisions/{id}/         → retrieve
- POST   /provisions/{id}/start/   → start (TECHNICIEN)
- POST   /provisions/{id}/complete/ → complete (TECHNICIEN)
- POST   /provisions/{id}/fail/    → fail (TECHNICIEN)
- POST   /provisions/{id}/retry/   → retry (TECHNICIEN)

SubscriptionViewSet:
- GET    /subscriptions/           → list
- GET    /subscriptions/{id}/      → retrieve
- GET    /subscriptions/expiring/  → expiring (30 jours)
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from ..models import Provision, Subscription
from ..serializers import (
    ProvisionSerializer,
    StartProvisioningSerializer,
    CompleteProvisioningSerializer,
    FailProvisioningSerializer,
    SubscriptionSerializer,
)
from ..selectors import (
    get_provisions_waiting,
    get_provisions_in_progress,
    get_active_subscriptions,
    get_expiring_subscriptions,
)
from ..services import (
    start_provisioning,
    complete_provisioning,
    fail_provisioning,
    retry_provisioning,
)
from ..permissions import IsTechnicienOrAdmin
from ..filters import ProvisionFilter, SubscriptionFilter


# ═══════════════════════════════════════════════════════════
# PROVISION VIEWSET
# ═══════════════════════════════════════════════════════════

class ProvisionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour Provision
    
    READ + actions workflow TECHNICIEN
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProvisionFilter
    search_fields = [
        'opportunity_line__product__title',
        'opportunity_line__opportunity__reference',
        'microsoft_subscription_id'
    ]
    ordering_fields = ['created_at', 'provisioning_started_at', 'provisioning_completed_at']
    ordering = ['-created_at']
    serializer_class = ProvisionSerializer
    
    def get_queryset(self):
        """
        Queryset avec RBAC + optimisation
        """
        user = self.request.user
        
        queryset = Provision.objects.select_related(
            'opportunity_line',
            'opportunity_line__opportunity',
            'opportunity_line__opportunity__client',
            'opportunity_line__product',
            'provisionned_by',
        ).prefetch_related(
            'subscription',
        )
        
        # RBAC filtering
        if user.role == 'TECHNICIEN':
            # Voit provisions :
            # - Qu'il a démarrées
            # - Assignées à lui
            # - WAITING_PROVISION (disponibles)
            from ..models import ProvisionStatus
            queryset = queryset.filter(
                provisionned_by=user
            ) | queryset.filter(
                opportunity_line__opportunity__assigned_to=user
            ) | queryset.filter(
                status=ProvisionStatus.WAITING_PROVISION
            )
        
        elif user.role == 'COMMERCIAL':
            # Voit provisions de ses opportunités
            queryset = queryset.filter(
                opportunity_line__opportunity__created_by=user
            ) | queryset.filter(
                opportunity_line__opportunity__assigned_to=user
            )
        
        elif user.role == 'FINANCE':
            # Voit toutes provisions opportunités APPROVED
            from ..models import OpportunityStatus
            queryset = queryset.filter(
                opportunity_line__opportunity__status=OpportunityStatus.APPROUVED
            )
        
        # ADMIN: voit tout
        
        return queryset.distinct()
    
    # ═══════════════════════════════════════════════════════
    # ACTIONS WORKFLOW (TECHNICIEN)
    # ═══════════════════════════════════════════════════════
    
    @action(
        detail=True,
        methods=['post'],
        url_path='start',
        permission_classes=[IsAuthenticated, IsTechnicienOrAdmin]
    )
    def start(self, request, pk=None):
        """
        POST /provisions/{id}/start/
        
        Démarre provisionnement (TECHNICIEN)
        
        Transition FSM: WAITING_PROVISION → PROVISIONING
        
        Input: {} (vide)
        """
        provision = self.get_object()
        
        # Utilise service
        provision = start_provisioning(
            provision_id=provision.id,
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Retourne
        serializer = self.get_serializer(provision)
        return Response(serializer.data)
    
    @action(
        detail=True,
        methods=['post'],
        url_path='complete',
        permission_classes=[IsAuthenticated, IsTechnicienOrAdmin]
    )
    def complete(self, request, pk=None):
        """
        POST /provisions/{id}/complete/
        
        Termine provisionnement avec succès (TECHNICIEN)
        
        Transition FSM: PROVISIONING → PROVISIONED
        
        Input:
            {
                "subscription_number": "abc-123-def",
                "start_date": "2024-01-01",
                "end_date": "2025-01-01"
            }
        """
        provision = self.get_object()
        
        # Valide input
        serializer = CompleteProvisioningSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Utilise service
        subscription = complete_provisioning(
            provision_id=provision.id,
            subscription_data=serializer.validated_data,
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Retourne Subscription créée
        output_serializer = SubscriptionSerializer(
            subscription,
            context={'request': request}
        )
        
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(
        detail=True,
        methods=['post'],
        url_path='fail',
        permission_classes=[IsAuthenticated, IsTechnicienOrAdmin]
    )
    def fail(self, request, pk=None):
        """
        POST /provisions/{id}/fail/
        
        Marque provisionnement comme échoué (TECHNICIEN)
        
        Transition FSM: PROVISIONING → ERROR
        
        Input:
            {
                "error_message": "Microsoft API timeout"
            }
        """
        provision = self.get_object()
        
        # Valide input
        serializer = FailProvisioningSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Utilise service
        provision = fail_provisioning(
            provision_id=provision.id,
            error_message=serializer.validated_data['error_message'],
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Retourne
        output_serializer = self.get_serializer(provision)
        return Response(output_serializer.data)
    
    @action(
        detail=True,
        methods=['post'],
        url_path='retry',
        permission_classes=[IsAuthenticated, IsTechnicienOrAdmin]
    )
    def retry(self, request, pk=None):
        """
        POST /provisions/{id}/retry/
        
        Retry provisionnement après échec (TECHNICIEN)
        
        Transition FSM: ERROR → PROVISIONING
        
        Input: {} (vide)
        """
        provision = self.get_object()
        
        # Utilise service
        provision = retry_provisioning(
            provision_id=provision.id,
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Retourne
        serializer = self.get_serializer(provision)
        return Response(serializer.data)
    
    # ═══════════════════════════════════════════════════════
    # ACTIONS LISTE
    # ═══════════════════════════════════════════════════════
    
    @action(detail=False, methods=['get'], url_path='waiting')
    def waiting(self, request):
        """
        GET /provisions/waiting/
        
        Liste provisions en attente (WAITING_PROVISION)
        
        Dashboard TECHNICIEN
        """
        provisions = get_provisions_waiting(user=request.user)
        
        serializer = self.get_serializer(provisions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='in-progress')
    def in_progress(self, request):
        """
        GET /provisions/in-progress/
        
        Liste provisions en cours (PROVISIONING)
        
        Dashboard TECHNICIEN
        """
        provisions = get_provisions_in_progress(user=request.user)
        
        serializer = self.get_serializer(provisions, many=True)
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


# ═══════════════════════════════════════════════════════════
# SUBSCRIPTION VIEWSET
# ═══════════════════════════════════════════════════════════

class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour Subscription
    
    READ-ONLY (création via ProvisionViewSet.complete)
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SubscriptionFilter
    search_fields = [
        'subscription_number',
        'provision__opportunity_line__product__title',
        'provision__opportunity_line__opportunity__reference'
    ]
    ordering_fields = ['created_at', 'start_date', 'end_date']
    ordering = ['-created_at']
    serializer_class = SubscriptionSerializer
    
    def get_queryset(self):
        """
        Queryset avec RBAC + optimisation
        """
        user = self.request.user
        
        queryset = Subscription.objects.select_related(
            'provision',
            'provision__opportunity_line',
            'provision__opportunity_line__opportunity',
            'provision__opportunity_line__opportunity__client',
            'provision__opportunity_line__product',
            'provision__provisionned_by',
        )
        
        # RBAC filtering
        if user.role == 'TECHNICIEN':
            # Voit subscriptions qu'il a provisionnées
            queryset = queryset.filter(provision__provisionned_by=user)
        
        elif user.role == 'COMMERCIAL':
            # Voit subscriptions de ses opportunités
            queryset = queryset.filter(
                provision__opportunity_line__opportunity__created_by=user
            ) | queryset.filter(
                provision__opportunity_line__opportunity__assigned_to=user
            )
        
        elif user.role == 'FINANCE':
            # Voit toutes subscriptions
            pass
        
        # ADMIN: voit tout
        
        return queryset.distinct()
    
    # ═══════════════════════════════════════════════════════
    # ACTIONS LISTE
    # ═══════════════════════════════════════════════════════
    
    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        """
        GET /subscriptions/active/
        
        Liste subscriptions actives (start_date <= today <= end_date)
        """
        subscriptions = get_active_subscriptions(user=request.user)
        
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='expiring')
    def expiring(self, request):
        """
        GET /subscriptions/expiring/
        
        Liste subscriptions expirant dans X jours
        
        Query params:
            ?days=30  (default: 30)
        
        Alertes renouvellement
        """
        days = int(request.query_params.get('days', 30))
        
        subscriptions = get_expiring_subscriptions(
            days=days,
            user=request.user
        )
        
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        GET /subscriptions/stats/
        
        Statistiques subscriptions
        
        Returns:
            {
                "total": 150,
                "active": 120,
                "expiring_30_days": 15,
                "expired": 30
            }
        """
        from datetime import date, timedelta
        
        queryset = self.get_queryset()
        today = date.today()
        
        stats = {
            'total': queryset.count(),
            'active': queryset.filter(
                start_date__lte=today,
                end_date__gte=today
            ).count(),
            'expiring_30_days': queryset.filter(
                end_date__gte=today,
                end_date__lte=today + timedelta(days=30)
            ).count(),
            'expired': queryset.filter(
                end_date__lt=today
            ).count(),
        }
        
        return Response(stats)
    
    @action(
        detail=False,
        methods=['get'],
        url_path='by-microsoft-id/(?P<microsoft_id>[^/.]+)'
    )
    def by_microsoft_id(self, request, microsoft_id=None):
        """
        GET /subscriptions/by-microsoft-id/{subscription_number}/
        
        Récupère subscription par Microsoft ID
        
        Utile pour lookup depuis portail Microsoft
        """
        from ..selectors import get_subscription_by_microsoft_id
        
        subscription = get_subscription_by_microsoft_id(microsoft_id)
        
        if not subscription:
            return Response(
                {'detail': 'Subscription introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifie permissions
        if request.user.role == 'COMMERCIAL':
            opp = subscription.provision.opportunity_line.opportunity
            if opp.created_by != request.user and opp.assigned_to != request.user:
                return Response(
                    {'detail': 'Action non autorisée'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        elif request.user.role == 'TECHNICIEN':
            if subscription.provision.provisionned_by != request.user:
                return Response(
                    {'detail': 'Action non autorisée'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Retourne
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)







"""
**✅ VIEWS PARTIE 4/5 COMPLETE !**

**Coverage Provision & Subscription ViewSets:**

### **ProvisionViewSet**
- ✅ LIST + RETRIEVE (ReadOnlyModelViewSet)
- ✅ **4 actions workflow TECHNICIEN:**
  - `start` - Démarre provisionnement
  - `complete` - Termine + crée Subscription
  - `fail` - Marque échec
  - `retry` - Retry après erreur
- ✅ **2 actions liste:**
  - `waiting` - Provisions WAITING_PROVISION
  - `in_progress` - Provisions PROVISIONING
- ✅ RBAC filtering (TECHNICIEN voit ses tâches)
- ✅ Permissions IsTechnicienOrAdmin sur actions

### **SubscriptionViewSet**
- ✅ LIST + RETRIEVE (ReadOnlyModelViewSet)
- ✅ **4 actions liste:**
  - `active` - Subscriptions actives
  - `expiring` - Expire dans X jours (default 30)
  - `stats` - Métriques dashboard
  - `by_microsoft_id` - Lookup par Microsoft ID
- ✅ RBAC filtering
- ✅ Query params support (days)

**Workflow TECHNICIEN complet:**
```
1. Dashboard TECHNICIEN:
   GET /provisions/waiting/
   → Liste tâches à faire

2. Démarrer provisionnement:
   POST /provisions/{id}/start/
   → FSM: WAITING_PROVISION → PROVISIONING

3a. Succès:
   POST /provisions/{id}/complete/
   {
     "subscription_number": "...",
     "start_date": "...",
     "end_date": "..."
   }
   → Crée Subscription
   → FSM: PROVISIONING → PROVISIONED

3b. Échec:
   POST /provisions/{id}/fail/
   {"error_message": "..."}
   → FSM: PROVISIONING → ERROR
   
   Puis retry:
   POST /provisions/{id}/retry/
   → FSM: ERROR → PROVISIONING
   """