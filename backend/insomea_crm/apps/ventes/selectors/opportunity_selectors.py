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
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from ..models import (
    Opportunity,
    OpportunityLine,
    OpportunityStatus,
    InsomeaQuote,
    InsomeaQuoteLine,
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
        
        elif user.role == 'FINANCE':
            # Finance voit :
            # - Opportunités CLIENT_PO_RECIEVED (à approuver)
            # - Opportunités APPROVED, INSOMEA_POS_SENT, INSOMEA_POS_CONFIRMED
            queryset = queryset.filter(
                Q(assigned_to=user) |
                Q(status__in=[
                    OpportunityStatus.CLIENT_PO_RECIEVED,
                    OpportunityStatus.APPROUVED,
                    OpportunityStatus.INSOMEA_POS_SENT,
                    OpportunityStatus.INSOMEA_POS_CONFIRMED,
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
        'related_opportunity',
        'client_purchase_order',
    )

    if prefetch_all:
        queryset = queryset.prefetch_related(
            Prefetch(
                'lines',
                queryset=OpportunityLine.objects.select_related(
                    'product',
                    'product__supplier',
                    'insomea_purchase_order',
                    'insomea_purchase_order__supplier',
                    'supplier_quote_line',
                    'supplier_quote_line__supplier_quote',
                    'supplier_quote_line__supplier_quote__supplier',
                    'insomea_quote_line',
                    'provision',
                ).order_by('created_at')
            ),
            Prefetch(
                'insomea_quote',
                queryset=InsomeaQuote.objects.prefetch_related(
                    Prefetch(
                        'lines',
                        queryset=InsomeaQuoteLine.objects.select_related(
                            'opportunity_line',
                            'supplier_quote_line',
                        )
                    )
                )
            ),
            'child_opportunities',
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
                OpportunityStatus.INSOMEA_POS_SENT,
                OpportunityStatus.INSOMEA_POS_CONFIRMED,
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

# ═══════════════════════════════════════════════════════════
# STATS (✅ CORRIGÉ)
# ═══════════════════════════════════════════════════════════

def get_opportunity_stats(user=None):
    """
    Statistiques opportunities
    
    ✅ CORRIGÉ: Revenue seulement si INSOMEA_PO_CONFIRMED+
    
    Args:
        user: User instance (RBAC)
    
    Returns:
        dict {
            'total_opportunities': int,
            'opportunities_this_month': int,
            'revenue_forecast': float,      # Toutes avec InsomeaQuote (prévisionnel)
            'revenue_confirmed': float,     # Seulement INSOMEA_PO_CONFIRMED+ (réalisé)
            'conversion_rate': float,
            'by_status': {status: count},
            'by_type': {type: count},
        }
    """
    
    queryset = get_opportunities_queryset(user=user, include_cancelled=False)
    
    # Total
    total = queryset.count()
    
    # This month
    today = timezone.now()
    first_day_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = queryset.filter(created_at__gte=first_day_month).count()
    
    # ✅ Revenue forecast (toutes avec InsomeaQuote - prévisionnel)
    revenue_forecast = Decimal('0.00')
    for opp in queryset.select_related('insomea_quote'):
        if hasattr(opp, 'insomea_quote') and opp.insomea_quote:
            revenue_forecast += opp.insomea_quote.total_sale
    
    # ✅ Revenue confirmed (seulement INSOMEA_PO_CONFIRMED+ - réalisé)
    confirmed_statuses = [
        OpportunityStatus.INSOMEA_POS_CONFIRMED,
    ]
    
    revenue_confirmed = Decimal('0.00')
    confirmed_opps = queryset.filter(status__in=confirmed_statuses).select_related('insomea_quote')
    for opp in confirmed_opps:
        if hasattr(opp, 'insomea_quote') and opp.insomea_quote:
            revenue_confirmed += opp.insomea_quote.total_sale
    
    # Conversion rate
    total_with_quote = queryset.filter(
        status__in=[
            OpportunityStatus.INSOMEA_QUOTE_CREATED,
            OpportunityStatus.CLIENT_PO_REQUEST,
            OpportunityStatus.CLIENT_PO_RECIEVED,
            OpportunityStatus.APPROUVED,
            OpportunityStatus.INSOMEA_POS_SENT,
            OpportunityStatus.INSOMEA_POS_CONFIRMED,
        ]
    ).count()
    
    conversion_rate = (total_with_quote / total) if total > 0 else 0.0
    
    # By status
    by_status = dict(
        queryset.values('status').annotate(
            count=Count('id')
        ).values_list('status', 'count')
    )
    
    # By type
    by_type = dict(
        queryset.values('type').annotate(
            count=Count('id')
        ).values_list('type', 'count')
    )
    
    return {
        'total_opportunities': total,
        'opportunities_this_month': this_month,
        'revenue_forecast': float(revenue_forecast),  # Prévisionnel
        'revenue_confirmed': float(revenue_confirmed),  # ✅ Réalisé
        'conversion_rate': round(conversion_rate, 2),
        'by_status': by_status,
        'by_type': by_type,
    }


def get_opportunity_pipeline_stats(user=None):
    """
    Stats pipeline (opportunités par étape workflow)
    
    ✅ CORRIGÉ: Value seulement si INSOMEA_PO_CONFIRMED
    
    Returns:
        list [
            {'status': 'DRAFT', 'status_display': 'Brouillon', 'count': 5, 'value': 0},
            {'status': 'INSOMEA_PO_CONFIRMED', 'status_display': '...', 'count': 3, 'value': 25000.00},
            ...
        ]
    """
    
    queryset = get_opportunities_queryset(user=user, include_cancelled=False)
    
    pipeline = []
    
    # Group by status
    status_groups = queryset.values('status').annotate(
        count=Count('id')
    )
    
    for group in status_groups:
        status = group['status']
        count = group['count']
        
        # ✅ Calculate value SEULEMENT si INSOMEA_PO_CONFIRMED
        value = Decimal('0.00')
        
        if status == OpportunityStatus.INSOMEA_POS_CONFIRMED:
            opps = queryset.filter(status=status).select_related('insomea_quote')
            for opp in opps:
                if hasattr(opp, 'insomea_quote') and opp.insomea_quote:
                    value += opp.insomea_quote.total_sale
        
        pipeline.append({
            'status': status,
            'status_display': dict(OpportunityStatus.choices).get(status, status),
            'count': count,
            'value': float(value),
        })
    
    # Sort by workflow order
    status_order = [
        OpportunityStatus.DRAFT,
        OpportunityStatus.SUPPLIER_QUOTE_REQUEST,
        OpportunityStatus.SUPPLIER_QUOTE_RECIEVED,
        OpportunityStatus.INSOMEA_QUOTE_CREATED,
        OpportunityStatus.CLIENT_PO_REQUEST,
        OpportunityStatus.CLIENT_PO_RECIEVED,
        OpportunityStatus.APPROUVED,
        OpportunityStatus.INSOMEA_POS_SENT,
        OpportunityStatus.INSOMEA_POS_CONFIRMED,
    ]
    
    pipeline_sorted = sorted(
        pipeline,
        key=lambda x: status_order.index(x['status']) if x['status'] in status_order else 999
    )
    
    return pipeline_sorted


def get_opportunity_revenue_chart(user=None, months=6):
    """
    Revenue chart data (monthly)
    
    ✅ CORRIGÉ: Revenue seulement INSOMEA_PO_CONFIRMED
    
    Args:
        user: User instance
        months: Number of months (default 6)
    
    Returns:
        list [
            {'month': '2024-01', 'month_display': 'January 2024', 'revenue': 50000.00, 'count': 10},
            ...
        ]
    """
    
    queryset = get_opportunities_queryset(user=user, include_cancelled=False)
    
    # ✅ Filtre seulement INSOMEA_PO_CONFIRMED
    queryset = queryset.filter(status=OpportunityStatus.INSOMEA_POS_CONFIRMED)
    
    # Get date range
    today = timezone.now()
    start_date = (today - timedelta(days=months * 30)).replace(day=1)
    
    # Filter opportunities created in period
    queryset = queryset.filter(created_at__gte=start_date)
    
    # Group by month
    revenue_data = []
    
    for i in range(months):
        month_date = today - timedelta(days=(months - i - 1) * 30)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Next month
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        
        # Filter
        month_opps = queryset.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).select_related('insomea_quote')
        
        # Calculate revenue
        revenue = Decimal('0.00')
        for opp in month_opps:
            if hasattr(opp, 'insomea_quote') and opp.insomea_quote:
                revenue += opp.insomea_quote.total_sale
        
        revenue_data.append({
            'month': month_start.strftime('%Y-%m'),
            'month_display': month_start.strftime('%B %Y'),
            'revenue': float(revenue),
            'count': month_opps.count(),
        })
    
    return revenue_data
