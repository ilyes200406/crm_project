"""
EXPLICATION :

Views = Endpoints API (Controllers)

Architecture :
- ViewSets DRF (REST standard)
- Views ultra-minces (logic dans services)
- Permissions strictes
- Filtres et pagination
- Actions custom

Principe SOLID :
Views orchestrent seulement :
1. Authentification/Permissions
2. Validation (via serializers)
3. Appel services (business logic)
4. Retour réponse

PAS de business logic dans views !

Performance :
- Queries optimisées (selectors)
- Pagination automatique
- Caching headers
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

from .models import Client, Contact, ClientActivity
from .serializers import (
    ClientListSerializer,
    ClientDetailSerializer,
    ClientCreateSerializer,
    ClientUpdateSerializer,
    ClientAssignSerializer,
    ClientStatsSerializer,
    ClientExportSerializer,
    ClientBulkUpdateSerializer,
    ClientBulkDeleteSerializer,
    ContactSerializer,
    ContactCreateSerializer,
    ContactMinimalSerializer,
    ClientActivitySerializer,
)
from .permissions import (
    ClientPermission,
    CanManageClient,
    CanManageContact,
    CanViewActivity,
    CanAssignClient,
    CanBulkUpdate,
    CanExportData,
)
from .filters import ClientFilter, ContactFilter, ClientActivityFilter
from .selectors import (
    get_clients_queryset,
    get_client_by_id,
    get_clients_with_stats,
    search_clients,
    get_client_stats,
    get_contacts_for_client,
    get_client_activities,
)
from .services import (
    create_client,
    update_client,
    delete_client,
    restore_client,
    assign_client,
    create_contact,
    update_contact,
    delete_contact,
)


# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def get_client_ip(request):
    """
    Récupère IP client pour audit
    
    Explication :
    Gère proxies/load balancers
    X-Forwarded-For header
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ═══════════════════════════════════════════════════════════
# CLIENT VIEWSET
# ═══════════════════════════════════════════════════════════

class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD complet pour clients
    
    Endpoints générés automatiquement :
    - GET    /clients/              → list()
    - POST   /clients/              → create()
    - GET    /clients/{id}/         → retrieve()
    - PUT    /clients/{id}/         → update()
    - PATCH  /clients/{id}/         → partial_update()
    - DELETE /clients/{id}/         → destroy()
    
    Actions custom :
    - POST   /clients/{id}/assign/        → assign()
    - POST   /clients/{id}/restore/       → restore()
    - GET    /clients/stats/              → stats()
    - GET    /clients/export/             → export()
    - POST   /clients/bulk-update/        → bulk_update()
    - POST   /clients/bulk-delete/        → bulk_delete()
    - GET    /clients/{id}/activities/    → activities()
    - GET    /clients/{id}/contacts/      → contacts()
    
    Explication ViewSet :
    Combine Router DRF + Mixins CRUD
    Génère URLs automatiquement
    Code DRY
    """
    
    # ───────────────────────────────────────────────────────
    # CONFIGURATION
    # ───────────────────────────────────────────────────────
    
    permission_classes = [IsAuthenticated] #, ClientPermission]
    # Explication :
    # IsAuthenticated : JWT valide requis
    # ClientPermission : RBAC custom
    
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    # Explication :
    # DjangoFilterBackend : Filtres déclaratifs
    # SearchFilter : Recherche full-text
    # OrderingFilter : Tri dynamique
    
    filterset_class = ClientFilter
    # Explication :
    # Classe de filtres custom
    # GET /clients/?status=CUSTOMER&industry=IT
    
    search_fields = ['company_name', 'email', 'phone', 'notes']
    # Explication :
    # GET /clients/?search=Dupont
    # Cherche dans ces champs
    
    ordering_fields = ['company_name', 'created_at', 'updated_at']
    ordering = ['-created_at']  # Default : plus récents
    # Explication :
    # GET /clients/?ordering=-created_at
    # GET /clients/?ordering=company_name
    
    lookup_field = 'id'
    # Explication :
    # Paramètre URL pour détails
    # /clients/{id}/ au lieu de /clients/{pk}/
    
    # ───────────────────────────────────────────────────────
    # QUERYSET OPTIMIZATION
    # ───────────────────────────────────────────────────────
    
    def get_queryset(self):
        """
        Retourne queryset optimisé avec filtrage RBAC
        
        Explication :
        Appelé automatiquement par DRF
        Applique filtres permissions
        Optimise queries
        
        Performance :
        - select_related : assigned_to, created_by
        - Filtre RBAC : commercial voit ses clients
        - Utilise selectors layer
        """
        
        user = self.request.user
        
        # Détecte action pour optimisation
        if self.action == 'list':
            # Liste : stats incluses
            queryset = get_clients_with_stats(user=user)
        elif self.action == 'retrieve':
            # Détails : prefetch contacts + activities
            queryset = get_clients_queryset(
                user=user,
                prefetch_contacts=True,
                prefetch_activities=True
            )
        else:
            # Autres : basique
            queryset = get_clients_queryset(user=user)
        
        return queryset
    
    # ───────────────────────────────────────────────────────
    # SERIALIZER SELECTION
    # ───────────────────────────────────────────────────────
    
    def get_serializer_class(self):
        """
        Retourne serializer selon action
        
        Explication :
        Différents serializers pour différentes actions
        Liste : léger
        Détails : complet
        Création : validation stricte
        
        Optimisation :
        Évite surcharge données inutiles
        """
        
        if self.action == 'list':
            return ClientListSerializer
        elif self.action == 'retrieve':
            return ClientDetailSerializer
        elif self.action == 'create':
            return ClientCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ClientUpdateSerializer
        elif self.action == 'assign':
            return ClientAssignSerializer
        elif self.action == 'export':
            return ClientExportSerializer
        elif self.action == 'bulk_update':
            return ClientBulkUpdateSerializer
        elif self.action == 'bulk_delete':
            return ClientBulkDeleteSerializer
        
        return ClientListSerializer
    
    # ───────────────────────────────────────────────────────
    # CRUD OPERATIONS
    # ───────────────────────────────────────────────────────
    
    def create(self, request, *args, **kwargs):
        """
        POST /clients/
        
        Explication :
        Override pour utiliser service layer
        
        Flow :
        1. Validation serializer
        2. Appel service create_client()
        3. Service gère : business logic + audit
        4. Retour 201 Created
        
        Sécurité :
        - Permission : ADMIN ou COMMERCIAL
        - Validation stricte
        - Audit automatique
        """
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Explication :
        # Validation via ClientCreateSerializer
        # raise_exception=True → 400 si invalide
        
        # Appel service (business logic)
        client = create_client(
            data=serializer.validated_data,
            user=request.user,
            ip_address=get_client_ip(request)
        )
        # Explication :
        # Service gère :
        # - Validation métier
        # - Création DB
        # - Log activité
        # - Normalisation données
        
        # Serialize pour réponse
        output_serializer = ClientDetailSerializer(client)
        
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )
        # Explication :
        # 201 Created = Ressource créée avec succès
        # Body = Client créé complet
    
    def update(self, request, *args, **kwargs):
        """
        PUT /clients/{id}/
        
        Explication :
        Update complet (tous les champs requis)
        """
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # Explication get_object() :
        # DRF built-in
        # 1. Récupère via queryset
        # 2. Vérifie has_object_permission()
        # 3. Retourne instance ou 404
        
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        
        # Appel service
        client = update_client(
            client_id=instance.id,
            data=serializer.validated_data,
            user=request.user,
            ip_address=get_client_ip(request)
        )
        
        output_serializer = ClientDetailSerializer(client)
        
        return Response(output_serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /clients/{id}/
        
        Explication :
        Update partiel (seulement champs fournis)
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """
        DELETE /clients/{id}/
        
        Explication :
        Soft delete (is_active=False)
        
        Sécurité :
        - Permission : ADMIN seulement
        - Pas de suppression physique
        - Garde toutes les relations
        """
        
        instance = self.get_object()
        
        # Appel service
        delete_client(
            client_id=instance.id,
            user=request.user,
            ip_address=get_client_ip(request)
        )
        # Explication :
        # Service vérifie permissions
        # is_active = False
        # Log activité
        
        return Response(
            {'message': f'Client "{instance.company_name}" désactivé avec succès.'},
            status=status.HTTP_200_OK
        )
        # Explication :
        # 200 OK au lieu de 204 No Content
        # Avec message confirmation
    
    # ───────────────────────────────────────────────────────
    # CUSTOM ACTIONS
    # ───────────────────────────────────────────────────────
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, CanAssignClient]
    )
    def assign(self, request, id=None):
        """
        POST /clients/{id}/assign/
        
        Réassigne client à un commercial
        
        Body : {assigned_to: uuid}
        
        Permission : ADMIN seulement
        
        Explication :
        @action custom endpoint
        detail=True : nécessite {id}
        methods=['post'] : seulement POST
        """
        
        client = self.get_object()
        
        serializer = ClientAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Appel service
        updated_client = assign_client(
            client_id=client.id,
            assigned_to_id=serializer.validated_data['assigned_to'],
            user=request.user,
            ip_address=get_client_ip(request)
        )
        
        output_serializer = ClientDetailSerializer(updated_client)
        
        return Response(output_serializer.data)
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, CanManageClient]
    )
    def restore(self, request, id=None):
        """
        POST /clients/{id}/restore/
        
        Réactive un client désactivé
        
        Permission : ADMIN seulement
        
        Explication :
        is_active = False → True
        Annule soft delete
        """
        
        # Récupère même si inactif
        try:
            client = Client.objects.get(id=id)
        except Client.DoesNotExist:
            return Response(
                {'error': 'Client non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Appel service
        restored_client = restore_client(
            client_id=client.id,
            user=request.user,
            ip_address=get_client_ip(request)
        )
        
        output_serializer = ClientDetailSerializer(restored_client)
        
        return Response({
            'message': f'Client "{restored_client.company_name}" réactivé avec succès.',
            'client': output_serializer.data
        })
    
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def stats(self, request):
        """
        GET /clients/stats/
        
        Statistiques dashboard
        
        Returns :
        {
            total_clients: int,
            by_status: {LEAD: X, PROSPECT: Y, ...},
            by_industry: {IT: X, FINANCE: Y, ...},
            recent_count: int
        }
        
        Explication :
        detail=False : pas de {id}
        /clients/stats/ au lieu de /clients/{id}/stats/
        
        Performance :
        Utilise selector avec aggregation SQL
        """
        
        stats = get_client_stats(user=request.user)
        serializer = ClientStatsSerializer(stats)
        
        return Response(serializer.data)
    
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, CanExportData]
    )
    def export(self, request):
        """
        GET /clients/export/?format=csv
        
        Export données clients
        
        Formats : CSV, Excel
        
        Permission : ADMIN, COMMERCIAL, FINANCE
        
        Explication :
        Génère fichier downloadable
        Format plat (pas de nested)
        
        Performance :
        Pagination ignorée pour export
        Max 10,000 records (limite sécurité)
        """
        
        # Récupère queryset filtré
        queryset = self.filter_queryset(self.get_queryset())
        
        # Limite sécurité
        queryset = queryset[:10000]
        
        # Serialize
        serializer = ClientExportSerializer(queryset, many=True)
        
        # Format export (CSV par défaut)
        export_format = request.query_params.get('format', 'csv')
        
        if export_format == 'csv':
            return self._export_csv(serializer.data)
        elif export_format == 'excel':
            return self._export_excel(serializer.data)
        else:
            return Response(
                {'error': 'Format non supporté. Utilisez csv ou excel'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _export_csv(self, data):
        """
        Génère CSV
        
        Explication :
        Utilise csv module Python
        Response avec Content-Type text/csv
        """
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        # Response CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="clients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        if not data:
            return response
        
        # Writer CSV
        writer = csv.DictWriter(response, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return response
    
    def _export_excel(self, data):
        """
        Génère Excel
        
        Explication :
        Utilise openpyxl
        Response avec Content-Type Excel
        """
        from openpyxl import Workbook
        from django.http import HttpResponse
        from datetime import datetime
        
        # Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Clients"
        
        if not data:
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="clients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
            wb.save(response)
            return response
        
        # Headers
        headers = list(data[0].keys())
        ws.append(headers)
        
        # Data
        for item in data:
            ws.append([item.get(h, '') for h in headers])
        
        # Response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="clients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        
        wb.save(response)
        return response
    
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated, CanBulkUpdate]
    )
    @transaction.atomic
    def bulk_update(self, request):
        """
        POST /clients/bulk-update/
        
        Update multiple clients
        
        Body : {
            client_ids: [uuid1, uuid2, ...],
            data: {status: 'CUSTOMER', ...}
        }
        
        Permission : ADMIN seulement
        
        Explication :
        @transaction.atomic : tout ou rien
        Limite 100 clients max (sécurité)
        
        Use case :
        Changement statut en masse
        Réassignation en masse
        """
        
        serializer = ClientBulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        client_ids = serializer.validated_data['client_ids']
        update_data = serializer.validated_data['data']
        
        # Récupère clients
        clients = Client.objects.filter(id__in=client_ids)
        
        if clients.count() != len(client_ids):
            return Response(
                {'error': 'Certains clients n\'existent pas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update chaque client via service
        updated = []
        for client in clients:
            try:
                updated_client = update_client(
                    client_id=client.id,
                    data=update_data,
                    user=request.user,
                    ip_address=get_client_ip(request)
                )
                updated.append(updated_client.id)
            except Exception as e:
                # Rollback automatique (transaction.atomic)
                return Response(
                    {'error': f'Erreur lors de la mise à jour : {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response({
            'message': f'{len(updated)} client(s) mis à jour avec succès',
            'updated_ids': updated
        })
    
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated, CanBulkUpdate]
    )
    @transaction.atomic
    def bulk_delete(self, request):
        """
        POST /clients/bulk-delete/
        
        Soft delete multiple clients
        
        Body : {client_ids: [uuid1, uuid2, ...]}
        
        Permission : ADMIN seulement
        
        Limite : 50 clients max
        """
        
        serializer = ClientBulkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        client_ids = serializer.validated_data['client_ids']
        
        # Récupère clients
        clients = Client.objects.filter(id__in=client_ids, is_active=True)
        
        # Soft delete via service
        deleted = []
        for client in clients:
            try:
                delete_client(
                    client_id=client.id,
                    user=request.user,
                    ip_address=get_client_ip(request)
                )
                deleted.append(client.id)
            except Exception as e:
                return Response(
                    {'error': f'Erreur lors de la suppression : {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response({
            'message': f'{len(deleted)} client(s) désactivé(s) avec succès',
            'deleted_ids': deleted
        })
    
    @action(
        detail=True,
        methods=['get'],
        permission_classes=[IsAuthenticated, CanViewActivity]
    )
    def activities(self, request, id=None):
        """
        GET /clients/{id}/activities/
        
        Historique activités client
        
        Pagination appliquée
        
        Explication :
        Endpoint nested pour activités
        Utilise selector optimisé
        """
        
        client = self.get_object()
        
        # Récupère activités
        activities = get_client_activities(client.id, limit=50)
        
        # Pagination
        page = self.paginate_queryset(activities)
        if page is not None:
            serializer = ClientActivitySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ClientActivitySerializer(activities, many=True)
        return Response(serializer.data)
    
    @action(
        detail=True,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def contacts(self, request, id=None):
        """
        GET /clients/{id}/contacts/
        
        Liste contacts du client
        
        Alternative à nested dans ClientDetailSerializer
        """
        
        client = self.get_object()
        
        # Récupère contacts
        contacts = get_contacts_for_client(client.id)
        
        serializer = ContactMinimalSerializer(contacts, many=True)
        return Response(serializer.data)


# ═══════════════════════════════════════════════════════════
# CONTACT VIEWSET
# ═══════════════════════════════════════════════════════════

class ContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD pour contacts
    
    Endpoints :
    - GET    /contacts/                    → list()
    - POST   /contacts/                    → create()
    - GET    /contacts/{id}/               → retrieve()
    - PUT    /contacts/{id}/               → update()
    - PATCH  /contacts/{id}/               → partial_update()
    - DELETE /contacts/{id}/               → destroy()
    
    Alternative : Nested sous clients
    /clients/{client_id}/contacts/
    
    Explication :
    ViewSet standard DRF
    Même pattern que ClientViewSet
    """
    
    queryset = Contact.objects.select_related('client').all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated] #, CanManageContact]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ContactFilter
    search_fields = ['first_name', 'last_name', 'email', 'position']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name', 'first_name']
    
    def get_serializer_class(self):
        """Serializer selon action"""
        if self.action == 'create':
            return ContactCreateSerializer
        return ContactSerializer
    
    def create(self, request, *args, **kwargs):
        """
        POST /contacts/
        
        Note : Nécessite client_id dans body
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Récupère client
        client_id = request.data.get('client')
        if not client_id:
            return Response(
                {'error': 'client_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        client = get_client_by_id(client_id, user=request.user, prefetch_all=False)
        
        # Appel service
        contact = create_contact(
            client_id=client.id,
            data=serializer.validated_data,
            user=request.user,
            ip_address=get_client_ip(request)
        )
        
        output_serializer = ContactSerializer(contact)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """PUT /contacts/{id}/"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Appel service
        contact = update_contact(
            contact_id=instance.id,
            data=serializer.validated_data,
            user=request.user,
            ip_address=get_client_ip(request)
        )
        
        output_serializer = ContactSerializer(contact)
        return Response(output_serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """DELETE /contacts/{id}/"""
        instance = self.get_object()
        
        # Appel service
        delete_contact(
            contact_id=instance.id,
            user=request.user,
            ip_address=get_client_ip(request)
        )
        
        return Response(
            {'message': 'Contact supprimé avec succès'},
            status=status.HTTP_200_OK
        )


# ═══════════════════════════════════════════════════════════
# CLIENT ACTIVITY VIEWSET
# ═══════════════════════════════════════════════════════════

class ClientActivityViewSet(viewsets.ReadOnlyModelViewSet):
    # ViewSet READ-ONLY pour activités
    
    # Endpoints :
    # - GET /activities/          → list()
    # - GET /activities/{id}/     → retrieve()
    
    # Explication :
    # ReadOnlyModelViewSet : Seulement GET
    # Pas de POST/PUT/DELETE (créées automatiquement)
    
    # Permission : Basée sur client parent
    
    queryset = ClientActivity.objects.select_related('client', 'user').all()
    serializer_class = ClientActivitySerializer
    permission_classes = [IsAuthenticated] #, CanViewActivity]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ClientActivityFilter
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):

        # Filtre selon permissions RBAC
        
        # Commercial : activités de ses clients
        # Autres : toutes les activités

        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role_id == 'COMMERCIAL':
            queryset = queryset.filter(client__assigned_to=user)
        
        return queryset
