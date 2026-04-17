"""
OPPORTUNITY PERMISSIONS

All permission classes for Opportunity and related objects (InsomeaQuote,
SupplierQuote, ClientPO, InsomeaPO).

Each class maps one action to one permission codename (seeded in the DB
by `python manage.py seed_permissions`).

Ownership rules summary:
    create / approve    → check_ownership=False  (no existing object / Finance
                          approves any opportunity, not just their own)
    update / delete /
    cancel / workflow   → check_ownership=True   (must be assigned_to or
                          created_by the opportunity)
    create_insomea_pos  → custom: Finance user must be the one who approved
                          this specific opportunity (approved_by == user)
"""

from ...users.permissions import HasVentesPerm


class CanViewOpportunity(HasVentesPerm):
    """
    Visibility rules differ by role:
        ADMIN      → everything
        COMMERCIAL → own opportunities (assigned_to or created_by)
        FINANCE    → CLIENT_PO_RECIEVED, APPROUVED, INSOMEA_POS_SENT, INSOMEA_POS_CONFIRMED
        TECHNICIEN → no opportunity access (provisions and subscriptions only)

    The queryset selector (get_all_opportunities) already pre-filters for
    COMMERCIAL and FINANCE so this has_object_permission guard is mainly for
    direct retrieve calls.
    """

    permission_codename = 'opportunity.view'

    def has_object_permission(self, request, view, obj):
        from ..models import Opportunity, OpportunityStatus

        user = request.user

        # Layer 3 — admin sees everything
        if user.role == 'ADMIN':
            return True

        # Resolve to Opportunity regardless of object type
        if isinstance(obj, Opportunity):
            opp = obj
        else:
            opp = getattr(obj, 'opportunity', None)
            if opp is None:
                return False

        # COMMERCIAL: ownership only
        if user.role == 'COMMERCIAL':
            return opp.assigned_to == user or opp.created_by == user

        # FINANCE: from client PO received onwards
        if user.role == 'FINANCE':
            return opp.status in [
                OpportunityStatus.CLIENT_PO_RECIEVED,
                OpportunityStatus.APPROUVED,
                OpportunityStatus.INSOMEA_POS_SENT,
                OpportunityStatus.INSOMEA_POS_CONFIRMED,
            ]

        # TECHNICIEN: no opportunity access
        return False


class CanCreateOpportunity(HasVentesPerm):
    """COMMERCIAL and ADMIN can open new opportunities."""
    permission_codename = 'opportunity.create'
    check_ownership = False   # no existing object at create time


class CanUpdateOpportunity(HasVentesPerm):
    """Only assigned/created COMMERCIAL (or ADMIN) can edit."""
    permission_codename = 'opportunity.update'
    check_ownership = True


class CanDeleteOpportunity(HasVentesPerm):
    """Only assigned/created COMMERCIAL (or ADMIN) can delete."""
    permission_codename = 'opportunity.delete'
    check_ownership = True


class CanCancelOpportunity(HasVentesPerm):
    """COMMERCIAL (owner) or FINANCE can cancel; ADMIN always can."""
    permission_codename = 'opportunity.cancel'
    check_ownership = True


class CanRequestSupplierQuotes(HasVentesPerm):
    """Opportunity owner (COMMERCIAL) triggers supplier quote requests."""
    permission_codename = 'opportunity.request_supplier_quotes'
    check_ownership = True


class CanCreateInsomeaQuote(HasVentesPerm):
    """Opportunity owner (COMMERCIAL) creates the Insomea quote."""
    permission_codename = 'opportunity.create_insomea_quote'
    check_ownership = True


class CanRequestClientPO(HasVentesPerm):
    """Opportunity owner sends the PO request to the client."""
    permission_codename = 'opportunity.request_client_po'
    check_ownership = True


class CanUploadClientPO(HasVentesPerm):
    """Opportunity owner uploads the received client PO."""
    permission_codename = 'opportunity.upload_client_po'
    check_ownership = True


class CanRollbackInsomeaQuote(HasVentesPerm):
    """
    Opportunity owner (COMMERCIAL) reverts INSOMEA_QUOTE_CREATED → SUPPLIER_QUOTE_RECIEVED
    to re-enter sale prices and regenerate the Insomea quote.
    """
    permission_codename = 'opportunity.rollback_insomea_quote'
    check_ownership = True


class CanApproveOpportunity(HasVentesPerm):
    """
    FINANCE approves any opportunity that reaches CLIENT_PO_RECIEVED.
    No ownership check — Finance doesn't own opportunities.
    """
    permission_codename = 'opportunity.approve'
    check_ownership = False


class CanCreateInsomeaPOs(HasVentesPerm):
    """
    Finance can only create Insomea POs for an opportunity that THEY approved.
    Custom has_object_permission checks opportunity.approved_by == user.
    """
    permission_codename = 'opportunity.create_insomea_pos'

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Layer 3 — admin override
        if user.role == 'ADMIN':
            return True

        # Layer 1 — Finance must have the codename
        if not user.has_ventes_perm(self.permission_codename):
            return False

        # Layer 2 — Finance must be the one who approved this specific opportunity
        return getattr(obj, 'approved_by', None) == user


class CanCreateSupplierQuote(HasVentesPerm):
    """COMMERCIAL creates per-line supplier quotes."""
    permission_codename = 'supplier_quote.create'
    check_ownership = True


class CanSendInsomeaPO(HasVentesPerm):
    """Finance sends an Insomea PO to the supplier."""
    permission_codename = 'insomea_po.send'
    check_ownership = False


class CanConfirmInsomeaPO(HasVentesPerm):
    """Finance records supplier confirmation of an Insomea PO."""
    permission_codename = 'insomea_po.confirm'
    check_ownership = False
