"""
SELECTORS - APP OPPORTUNITIES
"""

from .subscription_selectors import (
    get_all_subscriptions,
    get_subscription_by_id,
    get_subscription_by_number,
    get_active_subscriptions,
    get_pending_renewal_subscriptions,
    get_expired_subscriptions,
    get_expiring_subscriptions,
    get_subscriptions_by_client,
    get_subscriptions_by_product,
    get_subscriptions_needing_renewal,
    get_subscription_stats,
)

from .opportunity_selectors import (
    get_all_opportunities,
    get_opportunity_by_id,
    get_opportunity_stats,
    get_opportunity_pipeline_stats,
    get_opportunity_revenue_chart,
)

from .opportunity_line_selectors import (
    get_line_by_id,
)

from .quote_selectors import (
    get_supplier_quote_by_id,
    get_insomea_quote_by_id,
)

from .provision_selectors import (
    get_all_provisions,
    get_provision_by_id,
)

__all__ = [
    'get_all_subscriptions',
    'get_subscription_by_id',
    'get_subscription_by_number',
    'get_active_subscriptions',
    'get_pending_renewal_subscriptions',
    'get_expired_subscriptions',
    'get_expiring_subscriptions',
    'get_subscriptions_by_client',
    'get_subscriptions_by_product',
    'get_subscriptions_needing_renewal',
    'get_subscription_stats',

    'get_all_opportunities',
    'get_opportunity_by_id',
    'get_opportunity_stats',
    'get_opportunity_pipeline_stats',
    'get_opportunity_revenue_chart',

    'get_line_by_id',

    'get_supplier_quote_by_id',
    'get_insomea_quote_by_id',

    'get_all_provisions',
    'get_provision_by_id',
]