"""
PROVISION PERMISSIONS

Ownership model for provisions:
    start       → check_ownership=False  — any authorized TECHNICIEN can pick up
                  a WAITING provision; there is no owner yet.
    complete /
    fail /
    retry       → only the technician who STARTED the provision
                  (provision.provisionned_by == user) can continue it.
                  This prevents two technicians colliding on the same job.
"""

from ...users.permissions import HasVentesPerm


def _is_provision_owner(user, obj) -> bool:
    """Returns True if this user started (and thus owns) the provision."""
    return getattr(obj, 'provisionned_by', None) == user


class CanViewProvision(HasVentesPerm):
    """All authenticated roles can view provisions (read-only)."""
    permission_codename = 'provision.view'
    check_ownership = False


class CanStartProvisioning(HasVentesPerm):
    """
    Any authorized TECHNICIEN (or ADMIN) can claim a WAITING provision.
    No personal owner yet — first-come-first-served.
    """
    permission_codename = 'provision.start'
    check_ownership = False


class CanCompleteProvisioning(HasVentesPerm):
    """
    Only the technician who started the provision can mark it complete.
    Prevents a second tech from overwriting an in-progress job.
    """
    permission_codename = 'provision.complete'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role_id == 'ADMIN':                                   # Layer 3
            return True
        if not user.has_ventes_perm(self.permission_codename):     # Layer 1
            return False
        return _is_provision_owner(user, obj)                      # Layer 2


class CanFailProvisioning(HasVentesPerm):
    """Only the technician who started can report a provisioning failure."""
    permission_codename = 'provision.fail'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role_id == 'ADMIN':
            return True
        if not user.has_ventes_perm(self.permission_codename):
            return False
        return _is_provision_owner(user, obj)


class CanRetryProvisioning(HasVentesPerm):
    """Only the technician who originally started can retry after failure."""
    permission_codename = 'provision.retry'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role_id == 'ADMIN':
            return True
        if not user.has_ventes_perm(self.permission_codename):
            return False
        return _is_provision_owner(user, obj)
