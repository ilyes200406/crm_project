"""
RBAC INFRASTRUCTURE — Three-layer authorization base classes.

This file is the single source of truth for permission mechanics.
All concrete permission classes in ventes/permissions/ inherit from here.

────────────────────────────────────────────────────────────────────────────
THE THREE LAYERS (applied in order):

  Layer 1 — Role check (DB)
      User.has_ventes_perm(codename) queries the RolePermission table.
      Example: COMMERCIAL has 'opportunity.create', TECHNICIEN does not.

  Layer 2 — Ownership check (in-memory)
      For Opportunity / OpportunityLine, the user must be assigned_to or
      created_by the object.  Provision/Subscription objects have no personal
      owner so this layer is skipped for them (check_ownership=False).

  Layer 3 — Admin override
      If user.role == 'ADMIN', all checks are short-circuited and True
      is returned immediately — no DB query needed.

Combined rule:
    has_permission(codename)  AND  (owns_object OR is_admin)
────────────────────────────────────────────────────────────────────────────

USAGE IN SUBCLASSES:

    class CanCreateOpportunity(HasVentesPerm):
        permission_codename = 'opportunity.create'
        check_ownership = False   # no object exists yet at create time

    class CanUpdateOpportunity(HasVentesPerm):
        permission_codename = 'opportunity.update'
        check_ownership = True    # must own the opportunity
"""

from rest_framework.permissions import BasePermission


# ── Layer 2 helper ────────────────────────────────────────────────────────

def _is_owner(user, obj) -> bool:
    """
    Ownership check — Layer 2.

    Traverses to the parent Opportunity for nested objects so that a
    single helper covers all cases:
        Opportunity        → direct assigned_to / created_by check
        OpportunityLine    → delegates to its parent Opportunity
        Everything else    → returns True (role-only objects like Provision,
                             Subscription; ownership is tracked separately
                             via provisionned_by / approved_by and handled
                             in their own has_object_permission() overrides)
    """
    from ..ventes.models import Opportunity, OpportunityLine

    if isinstance(obj, Opportunity):
        return obj.assigned_to == user or obj.created_by == user

    if isinstance(obj, OpportunityLine):
        opp = obj.opportunity
        return opp.assigned_to == user or opp.created_by == user

    # Provision, Subscription, etc. — role alone is sufficient; their
    # concrete permission classes set check_ownership=False or override
    # has_object_permission() with a provisionned_by / approved_by check.
    return True


# ── Base permission class ─────────────────────────────────────────────────

class HasVentesPerm(BasePermission):
    """
    Base class for all ventes permission classes.

    Subclasses MUST set `permission_codename`.
    Subclasses MAY override `check_ownership` (default True) or
    override `has_object_permission()` for custom ownership logic.

    Attributes:
        permission_codename (str): e.g. 'opportunity.create'
        check_ownership (bool):
            True  → Layer 2 ownership applied in has_object_permission()
            False → role check is sufficient (create actions, Finance/Tech
                    actions that apply to any matching object)
    """

    permission_codename: str = None
    check_ownership: bool = True

    def has_permission(self, request, view):
        """
        Called on every request BEFORE the object is fetched.
        Checks Layer 1 (role has codename) + Layer 3 (admin bypass).
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.has_ventes_perm(self.permission_codename)

    def has_object_permission(self, request, view, obj):
        """
        Called after the object is fetched (retrieve, update, delete…).
        Applies Layer 3 → Layer 1 → Layer 2 in that order.
        """
        user = request.user

        # Layer 3 — admin override
        if user.role == 'ADMIN':
            return True

        # Layer 1 — role has the permission
        if not user.has_ventes_perm(self.permission_codename):
            return False

        # Layer 2 — ownership (skip if not required)
        if not self.check_ownership:
            return True

        return _is_owner(user, obj)


# ── Admin-only permission ─────────────────────────────────────────────────

class IsAdmin(BasePermission):
    """
    Grants access only to users with role=ADMIN.

    Used by users/api/views.py for user-management endpoints
    (create user, list users, etc.).
    """

    message = "Seuls les administrateurs peuvent effectuer cette action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'ADMIN'
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


# ── Standalone helpers (used in services / selectors / Celery tasks) ──────

def is_admin(user) -> bool:
    return bool(user and user.is_authenticated and user.role == 'ADMIN')


def is_commercial(user) -> bool:
    return bool(user and user.is_authenticated and user.role == 'COMMERCIAL')


def is_technicien(user) -> bool:
    return bool(user and user.is_authenticated and user.role == 'TECHNICIEN')


def is_finance(user) -> bool:
    return bool(user and user.is_authenticated and user.role == 'FINANCE')
