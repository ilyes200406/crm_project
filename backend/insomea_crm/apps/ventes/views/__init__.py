"""
VIEWS - APP OPPORTUNITIES

ViewSets REST API
"""

from .opportunity_views import OpportunityViewSet
from .line_views import OpportunityLineViewSet
from .quote_views import SupplierQuoteViewSet, InsomeaQuoteViewSet
from .provision_views import ProvisionViewSet
from .subscription_views import SubscriptionViewSet
from .workflow_views import StatusHistoryViewSet

__all__ = [
    'OpportunityViewSet',
    'OpportunityLineViewSet',
    'SupplierQuoteViewSet',
    'InsomeaQuoteViewSet',
    'ProvisionViewSet',
    'SubscriptionViewSet',
    'StatusHistoryViewSet',
    'SubscriptionViewSet',
]