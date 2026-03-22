"""
SELECTORS - QUOTES (Supplier & Insomea)

Queries optimisées devis
"""

from django.shortcuts import get_object_or_404

from ..models import (
    SupplierQuote,
    InsomeaQuote,
)


# ═══════════════════════════════════════════════════════════
# SUPPLIER QUOTE SELECTORS
# ═══════════════════════════════════════════════════════════

def get_supplier_quotes_for_opportunity(opportunity_id):
    """
    Récupère tous devis fournisseurs pour une opportunity
    
    Args:
        opportunity_id: UUID
    
    Returns:
        QuerySet SupplierQuote
    """
    return SupplierQuote.objects.filter(
        lines__opportunity_line__opportunity_id=opportunity_id
    ).select_related(
        'supplier',
        'created_by',
    ).prefetch_related(
        'lines',
        'lines__opportunity_line',
    ).distinct()


def get_supplier_quote_by_id(quote_id):
    """
    Récupère un devis fournisseur par ID
    
    Args:
        quote_id: UUID
    
    Returns:
        SupplierQuote instance
    
    Raises:
        Http404: Si n'existe pas
    """
    return get_object_or_404(
        SupplierQuote.objects.select_related(
            'supplier',
            'created_by',
        ).prefetch_related(
            'lines',
            'lines__opportunity_line',
            'lines__opportunity_line__product',
        ),
        id=quote_id
    )


# ═══════════════════════════════════════════════════════════
# INSOMEA QUOTE SELECTORS
# ═══════════════════════════════════════════════════════════

def get_insomea_quote_for_opportunity(opportunity_id):
    """
    Récupère devis Insomea pour une opportunity
    
    Args:
        opportunity_id: UUID
    
    Returns:
        InsomeaQuote instance ou None
    """
    try:
        return InsomeaQuote.objects.select_related(
            'opportunity',
            'created_by',
        ).prefetch_related(
            'lines',
            'lines__opportunity_line',
            'lines__opportunity_line__product',
            'lines__supplier_quote_line',
        ).get(opportunity_id=opportunity_id)
    except InsomeaQuote.DoesNotExist:
        return None


def get_insomea_quote_by_id(quote_id):
    """
    Récupère devis Insomea par ID
    
    Args:
        quote_id: UUID
    
    Returns:
        InsomeaQuote instance
    
    Raises:
        Http404: Si n'existe pas
    """
    return get_object_or_404(
        InsomeaQuote.objects.select_related(
            'opportunity',
            'created_by',
        ).prefetch_related(
            'lines',
            'lines__opportunity_line',
            'lines__opportunity_line__product',
            'lines__supplier_quote_line',
        ),
        id=quote_id
    )