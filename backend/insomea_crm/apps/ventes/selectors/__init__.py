"""
SELECTORS - APP OPPORTUNITIES
"""

# ... (garder imports existants)

# 🆕 NOUVEAU
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

__all__ = [
    # ... (garder existants)
    
    # 🆕 NOUVEAUX
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
]