"""
WORKFLOW VIEWS

StatusHistoryViewSet:
- GET    /status-history/                    → list (audit trail)
- GET    /status-history/{id}/               → retrieve
- GET    /status-history/by-opportunity/{id}/ → filter par opportunity
- GET    /status-history/by-user/{id}/       → filter par user
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from ..models import StatusHistory
from ..serializers import StatusHistorySerializer
from ..filters import StatusHistoryFilter


# ═══════════════════════════════════════════════════════════
# STATUS HISTORY VIEWSET
# ═══════════════════════════════════════════════════════════

class StatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour StatusHistory (audit trail)
    
    READ-ONLY (auto-créé via signals FSM)
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = StatusHistoryFilter
    search_fields = [
        'description',
        'transition_name',
        'opportunity__reference',
        'opportunity_line__product__title'
    ]
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    serializer_class = StatusHistorySerializer
    
    def get_queryset(self):
        """
        Queryset avec RBAC + optimisation
        """
        user = self.request.user
        
        queryset = StatusHistory.objects.select_related(
            'opportunity',
            'opportunity__client',
            'opportunity_line',
            'opportunity_line__product',
            'opportunity_line__opportunity',
            'provision',
            'provision__opportunity_line',
            'changed_by',
        )
        
        # RBAC filtering
        if user.role == 'COMMERCIAL':
            # Voit historique de ses opportunités
            from django.db.models import Q
            queryset = queryset.filter(
                Q(opportunity__created_by=user) |
                Q(opportunity__assigned_to=user) |
                Q(opportunity_line__opportunity__created_by=user) |
                Q(opportunity_line__opportunity__assigned_to=user) |
                Q(provision__opportunity_line__opportunity__created_by=user) |
                Q(provision__opportunity_line__opportunity__assigned_to=user)
            )
        
        elif user.role == 'TECHNICIEN':
            # Voit historique provisions qu'il gère
            from django.db.models import Q
            from ..models import OpportunityStatus
            
            queryset = queryset.filter(
                Q(provision__provisionned_by=user) |
                Q(opportunity__status=OpportunityStatus.APPROUVED) |
                Q(opportunity_line__opportunity__status=OpportunityStatus.APPROUVED)
            )
        
        elif user.role == 'FINANCE':
            # Voit historique opportunités en phase avancée
            from django.db.models import Q
            from ..models import OpportunityStatus
            
            allowed_statuses = [
                OpportunityStatus.CLIENT_PO_RECIEVED,
                OpportunityStatus.APPROUVED,
            ]
            
            queryset = queryset.filter(
                Q(opportunity__status__in=allowed_statuses) |
                Q(opportunity_line__opportunity__status__in=allowed_statuses) |
                Q(provision__opportunity_line__opportunity__status__in=allowed_statuses)
            )
        
        # ADMIN: voit tout
        
        return queryset.distinct()
    
    # ═══════════════════════════════════════════════════════
    # ACTIONS FILTER
    # ═══════════════════════════════════════════════════════
    
    @action(
        detail=False,
        methods=['get'],
        url_path='by-opportunity/(?P<opportunity_id>[^/.]+)'
    )
    def by_opportunity(self, request, opportunity_id=None):
        """
        GET /status-history/by-opportunity/{opportunity_id}/
        
        Historique complet d'une opportunité
        
        Inclut:
        - Transitions Opportunity
        - Transitions OpportunityLines
        - Transitions Provisions
        """
        from ..models import Opportunity
        from django.db.models import Q
        
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
        
        # Récupère historique complet
        history = self.get_queryset().filter(
            Q(opportunity=opportunity) |
            Q(opportunity_line__opportunity=opportunity) |
            Q(provision__opportunity_line__opportunity=opportunity)
        ).order_by('-created_at')
        
        # Paginate
        page = self.paginate_queryset(history)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)
    
    @action(
        detail=False,
        methods=['get'],
        url_path='by-user/(?P<user_id>[^/.]+)'
    )
    def by_user(self, request, user_id=None):
        """
        GET /status-history/by-user/{user_id}/
        
        Historique des actions d'un user
        
        Utile pour audit: "Qui a fait quoi ?"
        """
        from ...users.models import User
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Utilisateur introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifie permissions (ADMIN ou soi-même)
        if request.user.role != 'ADMIN' and request.user != user:
            return Response(
                {'detail': 'Action non autorisée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupère historique
        history = self.get_queryset().filter(
            changed_by=user
        ).order_by('-created_at')
        
        # Paginate
        page = self.paginate_queryset(history)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='recent')
    def recent(self, request):
        """
        GET /status-history/recent/
        
        Historique récent (24h)
        
        Dashboard activity feed
        """
        from datetime import timedelta
        from django.utils import timezone
        
        cutoff = timezone.now() - timedelta(hours=24)
        
        history = self.get_queryset().filter(
            created_at__gte=cutoff
        ).order_by('-created_at')[:50]  # Limité à 50
        
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        GET /status-history/stats/
        
        Statistiques audit trail
        
        Returns:
            {
                "total_changes": 1250,
                "changes_today": 45,
                "by_entity_type": {
                    "Opportunity": 400,
                    "OpportunityLine": 600,
                    "Provision": 250
                },
                "by_user": [
                    {"user": "John Doe", "count": 150},
                    ...
                ],
                "most_common_transitions": [
                    {"transition": "request_supplier_quote", "count": 120},
                    ...
                ]
            }
        """
        from datetime import date
        from django.db.models import Count
        
        queryset = self.get_queryset()
        today = date.today()
        
        # Total changes
        total = queryset.count()
        
        # Changes today
        changes_today = queryset.filter(created_at__date=today).count()
        
        # Par type entité
        by_entity = {}
        by_entity['Opportunity'] = queryset.filter(opportunity__isnull=False).count()
        by_entity['OpportunityLine'] = queryset.filter(opportunity_line__isnull=False).count()
        by_entity['Provision'] = queryset.filter(provision__isnull=False).count()
        
        # Par user (top 10)
        by_user = queryset.filter(
            changed_by__isnull=False
        ).values(
            'changed_by__first_name',
            'changed_by__last_name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        by_user_formatted = [
            {
                'user': f"{u['changed_by__first_name']} {u['changed_by__last_name']}",
                'count': u['count']
            }
            for u in by_user
        ]
        
        # Transitions les plus fréquentes
        transitions = queryset.filter(
            transition_name__isnull=False
        ).exclude(
            transition_name=''
        ).values('transition_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        transitions_formatted = [
            {'transition': t['transition_name'], 'count': t['count']}
            for t in transitions
        ]
        
        return Response({
            'total_changes': total,
            'changes_today': changes_today,
            'by_entity_type': by_entity,
            'by_user': by_user_formatted,
            'most_common_transitions': transitions_formatted,
        })