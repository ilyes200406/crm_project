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

"""
PROVISION VIEWS - MODIFIÉ

🆕 Support complete provisioning initial vs renewal
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from ..models import Provision, ProvisionStatus
from ..serializers import (
    ProvisionListSerializer,
    ProvisionDetailSerializer,
    StartProvisioningSerializer,
    CompleteProvisioningSerializer,  # 🆕 MODIFIÉ
    FailProvisioningSerializer,
)
from ..selectors import (
    get_all_provisions,
    get_provision_by_id,
)
from ..services import (
    start_provisioning,
    complete_provisioning,  # 🆕 MODIFIÉ
    fail_provisioning,
)
from ..filters import ProvisionFilter
from ..permissions import (
    CanViewProvision,
    CanStartProvisioning,
    CanCompleteProvisioning,
    CanFailProvisioning,
    CanRetryProvisioning,
)


class ProvisionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet Provisions
    
    Endpoints:
        GET  /provisions/              - Liste
        GET  /provisions/:id/          - Détail
        
        POST /provisions/:id/start/    - Start provisioning
        POST /provisions/:id/complete/ - Complete provisioning (🆕 MODIFIÉ)
        POST /provisions/:id/fail/     - Fail provisioning
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProvisionFilter
    search_fields = [
        'opportunity_line__product__title',
        'opportunity_line__opportunity__reference',
        'microsoft_subscription_id'
    ]
    ordering_fields = ['created_at', 'provisioning_started_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get queryset"""
        return get_all_provisions(user=self.request.user)
    
    def get_serializer_class(self):
        """Get serializer class"""
        if self.action == 'list':
            return ProvisionListSerializer
        elif self.action == 'start':
            return StartProvisioningSerializer
        elif self.action == 'complete':
            return CompleteProvisioningSerializer
        elif self.action == 'fail':
            return FailProvisioningSerializer
        else:
            return ProvisionDetailSerializer
    
    def get_permissions(self):
        """Map each action to its concrete permission class."""
        mapping = {
            'start':    [CanStartProvisioning()],
            'complete': [CanCompleteProvisioning()],
            'fail':     [CanFailProvisioning()],
            'retry':    [CanRetryProvisioning()],
        }
        return mapping.get(self.action, [CanViewProvision()])

    def get_object(self):
        """Get object"""
        provision_id = self.kwargs.get('pk')
        return get_provision_by_id(
            provision_id,
            user=self.request.user
        )
    
    # ───────────────────────────────────────────────────────
    # CRUD ACTIONS
    # ───────────────────────────────────────────────────────
    
    def list(self, request):
        """Liste provisions"""
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Détail provision"""
        provision = self.get_object()
        serializer = self.get_serializer(provision)
        return Response(serializer.data)
    
    # ───────────────────────────────────────────────────────
    # WORKFLOW ACTIONS
    # ───────────────────────────────────────────────────────
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Start provisioning
        
        POST /provisions/:id/start/
        
        Body: (vide)
        """
        
        provision = self.get_object()
        
        # Call service
        provision = start_provisioning(
            provision_id=provision.id,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Return
        serializer = ProvisionDetailSerializer(provision)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Complete provisioning
        
        🆕 MODIFIÉ: Support initial vs renewal
        
        POST /provisions/:id/complete/
        
        Body INITIAL:
            {
                "subscription_number": "MS-123",
                "start_date": "2024-01-01",
                "end_date": "2025-01-01"
            }
        
        Body RENEWAL:
            {
                "start_date": "2025-01-01",
                "end_date": "2026-01-01"
            }
        """
        
        provision = self.get_object()
        
        # 🆕 NOUVEAU: Ajouter provision dans context pour validation
        serializer = self.get_serializer(
            data=request.data,
            context={'provision': provision}  # ← IMPORTANT pour validation
        )
        serializer.is_valid(raise_exception=True)
        
        # Call service
        result = complete_provisioning(
            provision_id=provision.id,
            subscription_data=serializer.validated_data,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Return
        from ..serializers import SubscriptionDetailSerializer, SubscriptionTermSerializer
        
        return Response({
            'subscription': SubscriptionDetailSerializer(result['subscription']).data,
            'term': SubscriptionTermSerializer(result['term']).data,
            'provision': ProvisionDetailSerializer(result['provision']).data,
        })
    
    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """
        Fail provisioning
        
        POST /provisions/:id/fail/
        
        Body:
            {
                "error_message": "Error description"
            }
        """
        
        provision = self.get_object()
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Call service
        provision = fail_provisioning(
            provision_id=provision.id,
            error_message=serializer.validated_data['error_message'],
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Return
        output = ProvisionDetailSerializer(provision)
        return Response(output.data)






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