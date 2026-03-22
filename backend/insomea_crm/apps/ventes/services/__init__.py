"""
SERVICES - APP OPPORTUNITIES

Business Logic Layer
"""

from .opportunity_service import (
    create_opportunity,
    update_opportunity,
    delete_opportunity,
    add_line_to_opportunity,
    update_opportunity_line,
    remove_line_from_opportunity,
)

from .quote_service import (
    create_supplier_quote,
    create_insomea_quote,
    recalculate_supplier_quote_totals,
    recalculate_insomea_quote_totals,
)

from .purchase_order_service import (
    upload_client_po,
    create_insomea_pos,
)

from .provision_service import (
    create_provision_for_line,
    start_provisioning,
    complete_provisioning,
    fail_provisioning,
)

from .workflow_service import (
    request_all_supplier_quotes,
    request_client_po,
    approve_opportunity,
    update_opportunity_status_from_lines,
)

# 🆕 NOUVEAUX
from .subscription_service import (
    create_initial_subscription,
    renew_subscription,
    cancel_subscription,
    suspend_subscription,
    reactivate_subscription,
    check_subscription_expiring,
    get_subscription_revenue_metrics,
)

from .renewal_service import (
    create_renewal_opportunity,
    prepare_renewal_data_from_subscription,
    get_subscriptions_needing_renewal,
)

__all__ = [
    # Opportunity
    'create_opportunity',
    'update_opportunity',
    'delete_opportunity',
    'add_line_to_opportunity',
    'update_opportunity_line',
    'remove_line_from_opportunity',
    
    # Quotes
    'create_supplier_quote',
    'create_insomea_quote',
    'recalculate_supplier_quote_totals',
    'recalculate_insomea_quote_totals',
    
    # Purchase Orders
    'upload_client_po',
    'create_insomea_pos',
    
    # Provision
    'create_provision_for_line',
    'start_provisioning',
    'complete_provisioning',
    'fail_provisioning',
    
    # Workflow
    'request_all_supplier_quotes',
    'request_client_po',
    'approve_opportunity',
    'update_opportunity_status_from_lines',
    
    # 🆕 Subscription
    'create_initial_subscription',
    'renew_subscription',
    'cancel_subscription',
    'suspend_subscription',
    'reactivate_subscription',
    'check_subscription_expiring',
    'get_subscription_revenue_metrics',
    
    # 🆕 Renewal
    'create_renewal_opportunity',
    'prepare_renewal_data_from_subscription',
    'get_subscriptions_needing_renewal',
]