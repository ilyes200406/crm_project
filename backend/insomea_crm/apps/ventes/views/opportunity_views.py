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

"""
OPPORTUNITY VIEWS - MODIFIÉ

Support renewal workflow
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from ..models import OpportunityType  # 🆕 OpportunityType
from ..serializers import (
    CreateInsomeaQuoteSerializer,
    OpportunityListSerializer,
    OpportunityDetailSerializer,
    OpportunityCreateSerializer,
    OpportunityUpdateSerializer,
    RequestSupplierQuotesSerializer,
    RequestClientPOSerializer,
    ApproveOpportunitySerializer,
    CancelOpportunitySerializer,
    InsomeaPurchaseOrderListSerializer,
    UploadClientPOSerializer,
)
from ..selectors import (
    get_all_opportunities,
    get_opportunity_by_id,
)
from ..services import (
    create_opportunity,
    create_insomea_quote,
    update_opportunity,
    delete_opportunity,
    request_all_supplier_quotes,
    request_client_po,
    approve_opportunity,
    upload_client_po,
    update_insomea_quote_transition,
    confirm_all_insomea_pos,
    rollback_insomea_quote,
)
from ..filters import OpportunityFilter
from ..permissions import (
    CanViewOpportunity,
    CanCreateOpportunity,
    CanUpdateOpportunity,
    CanDeleteOpportunity,
    CanCancelOpportunity,
    CanRequestSupplierQuotes,
    CanCreateInsomeaQuote,
    CanRequestClientPO,
    CanUploadClientPO,
    CanUpdateInsomeaQuote,
    CanRollbackInsomeaQuote,
    CanApproveOpportunity,
    CanConfirmInsomeaPO,
)



class OpportunityViewSet(viewsets.ModelViewSet):
    """
    ViewSet Opportunités
    
    Endpoints:
        GET    /opportunities/              - Liste
        POST   /opportunities/              - Créer
        GET    /opportunities/:id/          - Détail
        PATCH  /opportunities/:id/          - Update
        DELETE /opportunities/:id/          - Delete
        
        🆕 GET    /opportunities/renewals/     - Liste RENEWAL
        🆕 GET    /opportunities/initials/     - Liste INITIAL
        🆕 GET    /opportunities/upsells/      - Liste UPSELL
        
        POST   /opportunities/:id/request_supplier_quotes/
        POST   /opportunities/:id/request_client_po/
        POST   /opportunities/:id/approve/
        POST   /opportunities/:id/cancel/
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OpportunityFilter
    search_fields = ['reference', 'name', 'client__company_name']
    ordering_fields = ['created_at', 'reference', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get queryset"""
        return get_all_opportunities(user=self.request.user)
    
    def get_serializer_class(self):
        """Get serializer class"""
        if self.action == 'list':
            return OpportunityListSerializer
        elif self.action == 'create':
            return OpportunityCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OpportunityUpdateSerializer
        elif self.action == 'request_supplier_quotes':
            return RequestSupplierQuotesSerializer
        elif self.action == 'request_client_po':
            return RequestClientPOSerializer
        elif self.action == 'create_insomea_quote':
            return CreateInsomeaQuoteSerializer
        elif self.action == 'upload_client_po':
            return UploadClientPOSerializer
        elif self.action == 'approve':
            return ApproveOpportunitySerializer
        elif self.action == 'cancel':
            return CancelOpportunitySerializer
        else:
            return OpportunityDetailSerializer
    
    def get_permissions(self):
        """Map each action to its concrete permission class."""
        mapping = {
            'create':                  [CanCreateOpportunity()],
            'update':                  [CanUpdateOpportunity()],
            'partial_update':          [CanUpdateOpportunity()],
            'destroy':                 [CanDeleteOpportunity()],
            'cancel':                  [CanCancelOpportunity()],
            'approve':                 [CanApproveOpportunity()],
            'request_supplier_quotes': [CanRequestSupplierQuotes()],
            'create_insomea_quote':    [CanCreateInsomeaQuote()],
            'request_client_po':       [CanRequestClientPO()],
            'upload_client_po':        [CanUploadClientPO()],
            'update_insomea_quote':    [CanUpdateInsomeaQuote()],
            'rollback_insomea_quote':  [CanRollbackInsomeaQuote()],
            'confirm_all_pos':         [CanConfirmInsomeaPO()],
        }
        return mapping.get(self.action, [CanViewOpportunity()])
    
    def get_object(self):
        """Get object"""
        opportunity_id = self.kwargs.get('pk')
        return get_opportunity_by_id(
            opportunity_id,
            user=self.request.user
        )
    
    # ───────────────────────────────────────────────────────
    # CRUD ACTIONS
    # ───────────────────────────────────────────────────────
    
    def list(self, request):
        """Liste opportunités"""
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """
        Créer opportunité
        
        Body:
            {
                "name": "Nom",
                "client": "uuid",
                "type": "INITIAL",  // 🆕 INITIAL, RENEWAL, UPSELL, DOWNGRADE
                "related_opportunity": "uuid",  // 🆕 Si RENEWAL
                "assigned_to": "uuid",
                "notes": ""
            }
        """
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Call service
        opportunity = create_opportunity(
            data=serializer.validated_data,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Return
        output = OpportunityDetailSerializer(opportunity)
        return Response(output.data, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """Détail opportunité"""
        opportunity = self.get_object()
        serializer = self.get_serializer(opportunity)
        return Response(serializer.data)
    
    def partial_update(self, request, pk=None):
        """Update opportunité"""
        opportunity = self.get_object()
        serializer = self.get_serializer(
            opportunity,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        
        # Call service
        opportunity = update_opportunity(
            opportunity_id=opportunity.id,
            data=serializer.validated_data,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Return
        output = OpportunityDetailSerializer(opportunity)
        return Response(output.data)
    
    def destroy(self, request, pk=None):
        """Delete opportunité"""
        opportunity = self.get_object()
        
        # Call service
        delete_opportunity(
            opportunity_id=opportunity.id,
            user=request.user
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    # ───────────────────────────────────────────────────────
    # 🆕 CUSTOM ACTIONS - TYPE FILTERS
    # ───────────────────────────────────────────────────────
    
    @action(detail=False, methods=['get'])
    def renewals(self, request):
        """
        Liste opportunités RENEWAL
        
        GET /opportunities/renewals/
        """
        
        queryset = self.filter_queryset(
            self.get_queryset().filter(type=OpportunityType.RENEWAL)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = OpportunityListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = OpportunityListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def initials(self, request):
        """
        Liste opportunités INITIAL
        
        GET /opportunities/initials/
        """
        
        queryset = self.filter_queryset(
            self.get_queryset().filter(type=OpportunityType.INITIAL)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = OpportunityListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = OpportunityListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upsells(self, request):
        """
        Liste opportunités UPSELL
        
        GET /opportunities/upsells/
        """
        
        queryset = self.filter_queryset(
            self.get_queryset().filter(type=OpportunityType.UPSELL)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = OpportunityListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = OpportunityListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    # ───────────────────────────────────────────────────────
    # WORKFLOW ACTIONS (INCHANGÉS)
    # ───────────────────────────────────────────────────────
    
    @action(detail=True, methods=['post'])
    def request_supplier_quotes(self, request, pk=None):
        """
        Demander devis fournisseurs
        
        POST /opportunities/:id/request_supplier_quotes/
        """
        
        opportunity = self.get_object()
        
        # Call service
        opportunity = request_all_supplier_quotes(
            opportunity_id=opportunity.id,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Return
        serializer = OpportunityDetailSerializer(opportunity)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_insomea_quote(self, request, pk=None):
        """Créer le devis client global pour l'opportunité."""
        opportunity = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        insomea_quote = create_insomea_quote(
            opportunity_id=opportunity.id,
            lines_pricing=serializer.validated_data['lines_pricing'],
            discount_percent=serializer.validated_data.get('discount_percent', 0),
            notes=serializer.validated_data.get('notes', ''),
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        refreshed = get_opportunity_by_id(opportunity.id, user=request.user)
        return Response({
            'opportunity': OpportunityDetailSerializer(refreshed).data,
            'insomea_quote_id': str(insomea_quote.id),
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def request_client_po(self, request, pk=None):
        """
        Demander BC client
        
        POST /opportunities/:id/request_client_po/
        """
        
        opportunity = self.get_object()
        
        # Call service
        opportunity = request_client_po(
            opportunity_id=opportunity.id,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Return
        serializer = OpportunityDetailSerializer(opportunity)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approuver opportunité (Finance)
        
        POST /opportunities/:id/approve/
        """
        
        opportunity = self.get_object()
        
        # Call service
        result = approve_opportunity(
            opportunity_id=opportunity.id,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'opportunity': OpportunityDetailSerializer(result['opportunity']).data,
            'pos_created': InsomeaPurchaseOrderListSerializer(
                result['pos_created'], 
                many=True
            ).data,
            'emails_sent': result['emails_sent'],
        })
    
    # 🆕 NOUVELLE ACTION
    @action(detail=True, methods=['post'])
    def confirm_all_pos(self, request, pk=None):
        """
        Confirmer tous les BC Insomea
        
        POST /opportunities/:id/confirm_all_pos/
        
        Body: (vide)
        
        🆕 NOUVEAU
        
        Flow:
            - Confirme toutes lignes INSOMEA_PO_SENT
            - Si toutes confirmées → crée provisions
        """
        
        opportunity = self.get_object()
        
        # Call service
        result = confirm_all_insomea_pos(
            opportunity_id=opportunity.id,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Return
        return Response({
            'lines_confirmed': result['lines_confirmed'],
            'provisions_created': result['provisions_created'],
            'opportunity': OpportunityDetailSerializer(result['opportunity']).data,
        })

    @action(detail=True, methods=['post'])
    def upload_client_po(self, request, pk=None):
        """Uploader le BC client reçu et faire avancer le workflow."""
        opportunity = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_po = upload_client_po(
            opportunity_id=opportunity.id,
            document=serializer.validated_data['document'],
            po_number=serializer.validated_data['po_number'],
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        refreshed = get_opportunity_by_id(opportunity.id, user=request.user)
        return Response({
            'opportunity': OpportunityDetailSerializer(refreshed).data,
            'client_po_id': str(client_po.id),
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def update_insomea_quote(self, request, pk=None):
        """
        Retract PO request to revise the Insomea quote (client negotiation)

        POST /opportunities/:id/update_insomea_quote/

        Transitions: CLIENT_PO_REQUEST → INSOMEA_QUOTE_CREATED
        """
        opportunity = self.get_object()

        opportunity = update_insomea_quote_transition(
            opportunity_id=opportunity.id,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        serializer = OpportunityDetailSerializer(opportunity)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def rollback_insomea_quote(self, request, pk=None):
        """
        Revenir à l'état SUPPLIER_QUOTE_RECIEVED pour modifier le devis Insomea.

        POST /opportunities/:id/rollback_insomea_quote/

        Transitions: INSOMEA_QUOTE_CREATED → SUPPLIER_QUOTE_RECIEVED
        Deletes the existing InsomeaQuote so a new one can be generated.
        """
        opportunity = self.get_object()

        rollback_insomea_quote(
            opportunity_id=opportunity.id,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        refreshed = get_opportunity_by_id(opportunity.id, user=request.user)
        serializer = OpportunityDetailSerializer(refreshed, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def regenerate_quote_pdf(self, request, pk=None):
        """
        Regenerate the InsomeaQuote PDF for this opportunity.

        POST /opportunities/:id/regenerate_quote_pdf/

        Returns the updated opportunity detail with the new document_url.
        """
        from ..models import OpportunityStatus
        from ..services.quote_service import generate_quote_pdf

        opportunity = self.get_object()

        try:
            insomea_quote = opportunity.insomea_quote
        except Exception:
            return Response(
                {'detail': 'Aucun devis Insomea trouvé pour cette opportunité.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            pdf_file = generate_quote_pdf(insomea_quote)
            insomea_quote.document.save(pdf_file.name, pdf_file, save=True)
        except Exception as e:
            return Response(
                {'detail': f'Erreur génération PDF : {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        refreshed = get_opportunity_by_id(opportunity.id, user=request.user)
        serializer = OpportunityDetailSerializer(refreshed, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Annuler opportunité

        POST /opportunities/:id/cancel/

        Body:
            {
                "reason": "Raison annulation"
            }
        """
        
        opportunity = self.get_object()
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reason = serializer.validated_data.get('reason')
        
        # Update
        opportunity.cancellation_reason = reason
        opportunity.cancel()
        opportunity.save()
        
        # Return
        output = OpportunityDetailSerializer(opportunity)
        return Response(output.data)

    # Dans OpportunityViewSet class

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Stats globales opportunités
    
        GET /opportunities/stats/
    
        Returns:
        {
            "total_opportunities": 45,
            "opportunities_this_month": 8,
            "revenue_forecast": 125000.00,
            "conversion_rate": 0.68,
            "by_status": {"DRAFT": 5, ...},
            "by_type": {"INITIAL": 30, ...}
        }
        """
        from ..selectors import get_opportunity_stats
    
        stats = get_opportunity_stats(user=request.user)
        return Response(stats)

    @action(detail=False, methods=['get'])
    def pipeline(self, request):
        """
        Pipeline stats (par status)
    
        GET /opportunities/pipeline/
    
        Returns:
            [
                {"status": "DRAFT", "status_display": "Brouillon", "count": 5, "value": 25000.00},
            ...
            ]
        """
        from ..selectors import get_opportunity_pipeline_stats
    
        pipeline = get_opportunity_pipeline_stats(user=request.user)
        return Response(pipeline)

    @action(detail=False, methods=['get'])
    def revenue_chart(self, request):
        """
        Revenue chart data
    
        GET /opportunities/revenue_chart/?months=6
    
        Query params:
            - months: int (default 6)
    
        Returns:
            [
                {"month": "2024-01", "month_display": "January 2024", "revenue": 50000.00, "count": 10},
                ...
            ]
        """
        from ..selectors import get_opportunity_revenue_chart
    
        months = int(request.query_params.get('months', 6))
        data = get_opportunity_revenue_chart(user=request.user, months=months)
        return Response(data)