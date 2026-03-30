"""
ventes/permissions/__init__.py

Re-exports all concrete permission classes so that views can use the
clean import:
    from ..permissions import CanCreateOpportunity, CanApproveOpportunity, …

This keeps imports backward-compatible if other code referenced the old
flat ventes/permissions.py file.
"""

from .opportunity import (
    CanViewOpportunity,
    CanCreateOpportunity,
    CanUpdateOpportunity,
    CanDeleteOpportunity,
    CanCancelOpportunity,
    CanRequestSupplierQuotes,
    CanCreateInsomeaQuote,
    CanRequestClientPO,
    CanUploadClientPO,
    CanUpdateInsomeaQuote,
    CanApproveOpportunity,
    CanCreateInsomeaPOs,
    CanCreateSupplierQuote,
)
from .provision import (
    CanViewProvision,
    CanStartProvisioning,
    CanCompleteProvisioning,
    CanFailProvisioning,
    CanRetryProvisioning,
)
from .subscription import (
    CanViewSubscription,
    CanCreateRenewal,
    CanCancelSubscription,
)

__all__ = [
    # Opportunity
    'CanViewOpportunity',
    'CanCreateOpportunity',
    'CanUpdateOpportunity',
    'CanDeleteOpportunity',
    'CanCancelOpportunity',
    'CanRequestSupplierQuotes',
    'CanCreateInsomeaQuote',
    'CanRequestClientPO',
    'CanUploadClientPO',
    'CanUpdateInsomeaQuote',
    'CanApproveOpportunity',
    'CanCreateInsomeaPOs',
    'CanCreateSupplierQuote',
    # Provision
    'CanViewProvision',
    'CanStartProvisioning',
    'CanCompleteProvisioning',
    'CanFailProvisioning',
    'CanRetryProvisioning',
    # Subscription
    'CanViewSubscription',
    'CanCreateRenewal',
    'CanCancelSubscription',
]
