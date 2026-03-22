"""
VIEWS - APP SUPPLIERS

ViewSets DRF pour API REST

Endpoints :
- GET /suppliers/ : Liste suppliers
- POST /suppliers/ : Créer supplier
- GET /suppliers/{id}/ : Détails supplier
- PUT/PATCH /suppliers/{id}/ : Modifier supplier
- DELETE /suppliers/{id}/ : Désactiver supplier
- POST /suppliers/{id}/activate/ : Activer supplier
- POST /suppliers/{id}/deactivate/ : Désactiver supplier
- GET /suppliers/stats/ : Statistiques
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Supplier
from .serializers import (
    SupplierListSerializer,
    SupplierDetailSerializer,
    SupplierCreateSerializer,
    SupplierUpdateSerializer,
    SupplierStatsSerializer,
)
from .permissions import SupplierPermission
from .filters import SupplierFilter
from .selectors import (
    get_suppliers_queryset,
    get_supplier_stats,
)
from .services import (
    create_supplier,
    update_supplier,
    activate_supplier,
    deactivate_supplier,
)


# ═══════════════════════════════════════════════════════════
# SUPPLIER VIEWSET
# ═══════════════════════════════════════════════════════════

class SupplierViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gestion suppliers
    
    Endpoints :
    - list : GET /suppliers/
    - create : POST /suppliers/
    - retrieve : GET /suppliers/{id}/
    - update : PUT /suppliers/{id}/
    - partial_update : PATCH /suppliers/{id}/
    - destroy : DELETE /suppliers/{id}/ (désactivation)
    - activate : POST /suppliers/{id}/activate/
    - deactivate : POST /suppliers/{id}/deactivate/
    - stats : GET /suppliers/stats/
    """
    
    permission_classes = [SupplierPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SupplierFilter
    search_fields = ['name', 'support_email']
    ordering_fields = ['name', 'type', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_queryset(self):
        """
        Retourne queryset filtré selon RBAC
        
        Tous les rôles peuvent voir tous les suppliers
        Pas de filtrage spécifique nécessaire
        """
        return get_suppliers_queryset(
            user=self.request.user,
            is_active=None  # Liste actifs ET inactifs
        )
    
    def get_serializer_class(self):
        """
        Retourne serializer approprié selon action
        
        Actions :
        - list : SupplierListSerializer (léger)
        - retrieve : SupplierDetailSerializer (complet)
        - create : SupplierCreateSerializer (validation stricte)
        - update/partial_update : SupplierUpdateSerializer
        """
        if self.action == 'list':
            return SupplierListSerializer
        elif self.action == 'retrieve':
            return SupplierDetailSerializer
        elif self.action == 'create':
            return SupplierCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SupplierUpdateSerializer
        
        return SupplierDetailSerializer
    
    # ───────────────────────────────────────────────────────
    # CREATE
    # ───────────────────────────────────────────────────────
    
    def create(self, request, *args, **kwargs):
        """
        POST /suppliers/
        
        Crée un nouveau supplier via service
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Appelle service pour création
        supplier = create_supplier(
            data=serializer.validated_data,
            user=request.user
        )
        
        # Retourne supplier créé
        output_serializer = SupplierDetailSerializer(supplier)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    # ───────────────────────────────────────────────────────
    # UPDATE
    # ───────────────────────────────────────────────────────
    
    def update(self, request, *args, **kwargs):
        """
        PUT /suppliers/{id}/
        
        Mise à jour complète via service
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        
        # Appelle service pour update
        supplier = update_supplier(
            supplier_id=instance.id,
            data=serializer.validated_data,
            user=request.user
        )
        
        output_serializer = SupplierDetailSerializer(supplier)
        return Response(output_serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /suppliers/{id}/
        
        Mise à jour partielle via service
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    # ───────────────────────────────────────────────────────
    # DELETE (Soft delete via désactivation)
    # ───────────────────────────────────────────────────────
    
    def destroy(self, request, *args, **kwargs):
        """
        DELETE /suppliers/{id}/
        
        Désactive le supplier (soft delete)
        Pas de suppression physique
        """
        instance = self.get_object()
        
        # Appelle service désactivation
        supplier = deactivate_supplier(
            supplier_id=instance.id,
            user=request.user
        )
        
        return Response(
            {'message': 'Fournisseur désactivé avec succès'},
            status=status.HTTP_200_OK
        )
    
    # ───────────────────────────────────────────────────────
    # CUSTOM ACTIONS
    # ───────────────────────────────────────────────────────
    
    @action(
        detail=True,
        methods=['post'],
        url_path='activate'
    )
    def activate(self, request, pk=None):
        """
        POST /suppliers/{id}/activate/
        
        Active un supplier désactivé
        
        Permissions : ADMIN, FINANCE
        """
        supplier = self.get_object()
        
        # Appelle service activation
        supplier = activate_supplier(
            supplier_id=supplier.id,
            user=request.user
        )
        
        serializer = SupplierDetailSerializer(supplier)
        return Response(serializer.data)
    
    @action(
        detail=True,
        methods=['post'],
        url_path='deactivate'
    )
    def deactivate(self, request, pk=None):
        """
        POST /suppliers/{id}/deactivate/
        
        Désactive un supplier
        
        Permissions : ADMIN
        """
        supplier = self.get_object()
        
        # Appelle service désactivation
        supplier = deactivate_supplier(
            supplier_id=supplier.id,
            user=request.user
        )
        
        serializer = SupplierDetailSerializer(supplier)
        return Response(serializer.data)
    
    @action(
        detail=False,
        methods=['get'],
        url_path='stats'
    )
    def stats(self, request):
        """
        GET /suppliers/stats/
        
        Retourne statistiques suppliers
        
        Stats :
        - total_suppliers
        - by_type (DIRECT, DISTRIBUTOR, RESELLER)
        - active_count
        - inactive_count
        """
        stats = get_supplier_stats(user=request.user)
        serializer = SupplierStatsSerializer(stats)
        return Response(serializer.data)