"""
SELECTORS - OPPORTUNITIES & LINES

Queries optimisées avec:
- select_related (FK)
- prefetch_related (reverse FK)
- RBAC filtering
- Annotations
"""

from django.db.models import Q, Prefetch, Count, Sum, Avg
from django.shortcuts import get_object_or_404

from ..models import (
    Opportunity,
    OpportunityLine,
    OpportunityStatus,
)

#from ..models import StatusHistory


# ═══════════════════════════════════════════════════════════
# OPPORTUNITY QUERIES
# ═══════════════════════════════════════════════════════════

def get_opportunities_queryset(user=None, filters=None, include_cancelled=False, prefetch_lines=False, prefetch_quotes=False, prefetch_history=False):

    queryset = Opportunity.objects.all()
    queryset = queryset.select_related('client', 'created_by', 'assigned_to',)
    
    if prefetch_lines:
        queryset = queryset.prefetch_related(
            Prefetch(
                'lines',
                queryset=OpportunityLine.objects.select_related(
                    'product',
                    'insomea_purchase_order',
                ).order_by('created_at')
            )
        )
    
    if prefetch_quotes:
        queryset = queryset.prefetch_related(
            'insomea_quote',
            'client_purchase_order',
        )
    """
    if prefetch_history:
        queryset = queryset.prefetch_related(
            Prefetch(
                'status_history',
                queryset=StatusHistory.objects.select_related('changed_by').order_by('-created_at')[:20]
            )
        )
    """
    # Filtre cancelled
    if not include_cancelled:
        queryset = queryset.exclude(status=OpportunityStatus.CANCELLED)
    
    # Filtres RBAC (selon rôle user)
    if user:
        if user.role == 'COMMERCIAL':
            # Commercial voit :
            # - Opportunités qu'il a créées
            # - Opportunités qui lui sont assignées
            queryset = queryset.filter(
                Q(created_by=user) | Q(assigned_to=user)
            )
        
        elif user.role == 'TECHNICIEN':
            # Technicien voit :
            # - Opportunités APPROVED (à provisionner)
            # - Opportunités qui lui sont assignées
            queryset = queryset.filter(
                Q(assigned_to=user) |
                Q(status=OpportunityStatus.APPROUVED)
            )
        
        elif user.role == 'FINANCE':
            # Finance voit :
            # - Opportunités CLIENT_PO_RECIEVED (à approuver)
            # - Opportunités APPROVED
            # - Toutes pour reporting
            queryset = queryset.filter(
                Q(assigned_to=user) |
                Q(status__in=[
                    OpportunityStatus.CLIENT_PO_RECIEVED,
                    OpportunityStatus.APPROUVED,
                ])
            )
        
        # ADMIN : voit tout (pas de filtre)
    
    # Filtres additionnels
    if filters:
        queryset = queryset.filter(**filters)
    
    return queryset

def get_all_opportunities(*, user=None):
    return get_opportunities_queryset(user=user, include_cancelled=False)


def get_opportunity_by_id(opportunity_id, user=None, prefetch_all=True):
    """
    Récupère UNE opportunity par ID avec RBAC check
    
    Args:
        opportunity_id: UUID
        user: User instance (pour RBAC)
        prefetch_all: bool précharger toutes relations
    
    Returns:
        Opportunity instance
    
    Raises:
        Http404: Si n'existe pas ou pas accès
    """
    
    queryset = Opportunity.objects.select_related(
        'client',
        'created_by',
        'assigned_to',
    )
    
    if prefetch_all:
        queryset = queryset.prefetch_related(
            Prefetch(
                'lines',
                queryset=OpportunityLine.objects.select_related(
                    'product',
                    'insomea_purchase_order',
                    'supplier_quote_line',
                    'provision',
                ).prefetch_related(
                ).order_by('created_at')
            ),
            'insomea_quote',
            'client_purchase_order',
        )
    
    # Récupère
    opportunity = get_object_or_404(queryset, id=opportunity_id)
    
    # RBAC check
    if user:
        if user.role == 'COMMERCIAL':
            if opportunity.created_by != user and opportunity.assigned_to != user:
                from django.http import Http404
                raise Http404("Opportunité non trouvée")
        
        elif user.role == 'TECHNICIEN':
            if opportunity.status != OpportunityStatus.APPROUVED and opportunity.assigned_to != user:
                from django.http import Http404
                raise Http404("Opportunité non trouvée")
        
        elif user.role == 'FINANCE':
            allowed_statuses = [
                OpportunityStatus.CLIENT_PO_RECIEVED,
                OpportunityStatus.APPROUVED,
            ]
            if opportunity.status not in allowed_statuses and opportunity.assigned_to != user:
                from django.http import Http404
                raise Http404("Opportunité non trouvée")
    
    return opportunity


def get_opportunity_by_reference(reference, user=None):
    """
    Récupère opportunity par référence
    
    Args:
        reference: str (ex: OPP-2024-00001)
        user: User instance (RBAC)
    
    Returns:
        Opportunity instance ou None
    """
    try:
        queryset = Opportunity.objects.select_related(
            'client',
            'created_by',
            'assigned_to',
        )
        
        opportunity = queryset.get(reference__iexact=reference)
        
        # RBAC check
        if user and user.role == 'COMMERCIAL':
            if opportunity.created_by != user and opportunity.assigned_to != user:
                return None
        
        return opportunity
        
    except Opportunity.DoesNotExist:
        return None


# ═══════════════════════════════════════════════════════════
# SEARCH QUERIES
# ═══════════════════════════════════════════════════════════

def search_opportunities(search_term, user=None, limit=20):
    """
    Recherche full-text opportunities
    
    Cherche dans:
    - reference
    - name
    - client.company_name
    - notes
    
    Args:
        search_term: str
        user: User instance (RBAC)
        limit: int max results
    
    Returns:
        QuerySet
    """
    
    queryset = get_opportunities_queryset(user=user, include_cancelled=False)
    
    if not search_term:
        return queryset[:limit]
    
    query = Q(reference__icontains=search_term) | \
            Q(name__icontains=search_term) | \
            Q(client__company_name__icontains=search_term) | \
            Q(notes__icontains=search_term)
    
    queryset = queryset.filter(query)
    
    # Tri par pertinence
    queryset = queryset.extra(
        select={
            'relevance': """
                CASE 
                    WHEN reference ILIKE %s THEN 1
                    WHEN name ILIKE %s THEN 2
                    ELSE 3
                END
            """
        },
        select_params=[f'%{search_term}%'] * 2
    ).order_by('relevance', '-created_at')
    
    return queryset[:limit]


def get_opportunities_by_status(status, user=None):
    """
    Récupère opportunities par statut
    
    Args:
        status: OpportunityStatus choice
        user: User instance (RBAC)
    
    Returns:
        QuerySet
    """
    return get_opportunities_queryset(
        user=user,
        filters={'status': status},
        include_cancelled=True if status == OpportunityStatus.CANCELLED else False
    )


def get_opportunities_needing_attention(user):
    """
    Récupère opportunities nécessitant action
    
    Intelligent selon rôle:
    - COMMERCIAL: DRAFT → CLIENT_PO_REQUEST
    - FINANCE: CLIENT_PO_RECIEVED
    - TECHNICIEN: APPROUVED
    
    Args:
        user: User instance
    
    Returns:
        QuerySet
    """
    
    queryset = get_opportunities_queryset(user=user, include_cancelled=False)
    
    if user.role == 'COMMERCIAL':
        queryset = queryset.filter(
            Q(created_by=user) | Q(assigned_to=user)
        ).filter(
            status__in=[
                OpportunityStatus.DRAFT,
                OpportunityStatus.SUPPLIER_QUOTE_REQUEST,
                OpportunityStatus.SUPPLIER_QUOTE_RECIEVED,
                OpportunityStatus.INSOMEA_QUOTE_CREATED,
                OpportunityStatus.CLIENT_PO_REQUEST,
            ]
        )
    
    elif user.role == 'FINANCE':
        queryset = queryset.filter(
            status=OpportunityStatus.CLIENT_PO_RECIEVED
        )
    
    elif user.role == 'TECHNICIEN':
        queryset = queryset.filter(
            status=OpportunityStatus.APPROUVED
        )
    
    else:  # ADMIN
        queryset = queryset.exclude(
            status__in=[OpportunityStatus.APPROUVED, OpportunityStatus.CANCELLED]
        )
    
    return queryset.order_by('created_at')


# ═══════════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════════

def get_opportunity_stats(user=None):
    """
    Statistiques opportunities
    
    Args:
        user: User instance (RBAC)
    
    Returns:
        dict avec stats
    """
    
    queryset = get_opportunities_queryset(user=user, include_cancelled=False)
    
    # Total
    total = queryset.count()
    
    # Par statut
    by_status = dict(
        queryset.values('status').annotate(
            count=Count('id')
        ).values_list('status', 'count')
    )
    
    return {
        'total_opportunities': total,
        'by_status': by_status,
    }
