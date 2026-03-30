"""
SUBSCRIPTION PERMISSIONS

Subscriptions are company-wide resources — they are not personally owned
by any one user.  All checks are role-only (check_ownership=False).

    view            → COMMERCIAL, FINANCE, TECHNICIEN, ADMIN
    create_renewal  → COMMERCIAL, ADMIN  (they initiate the renewal sale)
    cancel          → FINANCE, ADMIN     (Finance decides to terminate)
"""

from ...users.permissions import HasVentesPerm


class CanViewSubscription(HasVentesPerm):
    """All roles can view subscriptions."""
    permission_codename = 'subscription.view'
    check_ownership = False


class CanCreateRenewal(HasVentesPerm):
    """COMMERCIAL creates a renewal opportunity from an expiring subscription."""
    permission_codename = 'subscription.create_renewal'
    check_ownership = False


class CanCancelSubscription(HasVentesPerm):
    """FINANCE (or ADMIN) can cancel a subscription."""
    permission_codename = 'subscription.cancel'
    check_ownership = False
