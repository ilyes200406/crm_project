from rest_framework.permissions import BasePermission


# ── Layer 2 helper ────────────────────────────────────────────────────────

def _is_owner(user, obj) -> bool:
    from ..ventes.models import Opportunity, OpportunityLine

    if isinstance(obj, Opportunity):
        return obj.assigned_to == user or obj.created_by == user

    if isinstance(obj, OpportunityLine):
        opp = obj.opportunity
        return opp.assigned_to == user or opp.created_by == user

    return True


# ── Base permission class ─────────────────────────────────────────────────

class HasVentesPerm(BasePermission):
    permission_codename: str = None
    check_ownership: bool = True

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.has_ventes_perm(self.permission_codename)

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role_id == 'ADMIN':
            return True

        if not user.has_ventes_perm(self.permission_codename):
            return False

        if not self.check_ownership:
            return True

        return _is_owner(user, obj)


# ── Admin-only permission ─────────────────────────────────────────────────

class IsAdmin(BasePermission):
    message = "Seuls les administrateurs peuvent effectuer cette action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role_id == 'ADMIN'
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


# ── Standalone helpers (used in services / selectors / Celery tasks) ──────

def is_admin(user) -> bool:
    return bool(user and user.is_authenticated and user.role_id == 'ADMIN')


def is_commercial(user) -> bool:
    return bool(user and user.is_authenticated and user.role_id == 'COMMERCIAL')


def is_technicien(user) -> bool:
    return bool(user and user.is_authenticated and user.role_id == 'TECHNICIEN')


def is_finance(user) -> bool:
    return bool(user and user.is_authenticated and user.role_id == 'FINANCE')
