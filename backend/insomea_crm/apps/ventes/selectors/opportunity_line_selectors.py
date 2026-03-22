from django.db.models import Q, Prefetch, Count, Sum, Avg
from django.shortcuts import get_object_or_404

from ..models import (
    Opportunity,
    OpportunityLine,
    OpportunityStatus,
    OpportunityLineStatus,
)

from ..models import StatusHistory


def get_lines_for_opportunity(opportunity_id):
    """
    Récupère toutes les lignes d'une opportunity
    
    Args:
        opportunity_id: UUID
    
    Returns:
        QuerySet OpportunityLine
    """
    return OpportunityLine.objects.filter(
        opportunity_id=opportunity_id
    ).select_related(
        'product',
        'opportunity',
        'insomea_purchase_order',
    ).prefetch_related(
        'supplier_quote_line',
        'provision',
    ).order_by('created_at')


def get_line_by_id(line_id):
    """
    Récupère une ligne par ID
    
    Args:
        line_id: UUID
    
    Returns:
        OpportunityLine instance
    
    Raises:
        Http404: Si n'existe pas
    """
    return get_object_or_404(
        OpportunityLine.objects.select_related(
            'opportunity',
            'opportunity__client',
            'product',
            'insomea_purchase_order',
        ).prefetch_related(
            'supplier_quote_line',
            'provision',
        ),
        id=line_id
    )


def get_lines_by_status(status, opportunity_id=None):
    """
    Récupère lignes par statut
    
    Args:
        status: OpportunityLineStatus choice
        opportunity_id: UUID (optionnel, filtre par opportunity)
    
    Returns:
        QuerySet OpportunityLine
    """
    queryset = OpportunityLine.objects.filter(status=status)
    
    if opportunity_id:
        queryset = queryset.filter(opportunity_id=opportunity_id)
    
    return queryset.select_related('product', 'opportunity')