"""
SELECTORS - APP OPPORTUNITIES

Queries optimisées READ-ONLY
"""

from .opportunity_selectors import (
    get_opportunities_queryset,
    get_opportunity_by_id,
    get_opportunity_by_reference,
    search_opportunities,
    get_opportunities_by_status,
    get_opportunities_needing_attention,
    get_opportunity_stats,
    get_lines_for_opportunity,
    get_line_by_id,
    get_lines_by_status,
)

from .quote_selectors import (
    get_supplier_quotes_for_opportunity,
    get_supplier_quote_by_id,
    get_insomea_quote_for_opportunity,
    get_insomea_quote_by_id,
)

from .provision_selectors import (
    get_provisions_waiting,
    get_provisions_in_progress,
    get_provision_by_id,
    get_active_subscriptions,
    get_expiring_subscriptions,
    get_subscription_by_id,
    get_subscription_by_microsoft_id,
)

__all__ = [
    # Opportunity
    'get_opportunities_queryset',
    'get_opportunity_by_id',
    'get_opportunity_by_reference',
    'search_opportunities',
    'get_opportunities_by_status',
    'get_opportunities_needing_attention',
    'get_opportunity_stats',
    
    # OpportunityLine
    'get_lines_for_opportunity',
    'get_line_by_id',
    'get_lines_by_status',
    
    # Quotes
    'get_supplier_quotes_for_opportunity',
    'get_supplier_quote_by_id',
    'get_insomea_quote_for_opportunity',
    'get_insomea_quote_by_id',
    
    # Provision
    'get_provisions_waiting',
    'get_provisions_in_progress',
    'get_provision_by_id',
    
    # Subscription
    'get_active_subscriptions',
    'get_expiring_subscriptions',
    'get_subscription_by_id',
    'get_subscription_by_microsoft_id',
]