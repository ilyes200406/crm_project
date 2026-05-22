from rest_framework.permissions import BasePermission


class IsCommercialOrAdmin(BasePermission):
    message = "Seuls les commerciaux et administrateurs peuvent accéder aux demandes."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role_id in ('COMMERCIAL', 'ADMIN')
        )


class IsAssignedCommercialOrAdmin(BasePermission):
    """Pour les actions sur une demande déjà prise en charge."""
    message = "Vous n'êtes pas autorisé à modifier cette demande."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role_id == 'ADMIN':
            return True
        return obj.prise_en_charge_par == user
