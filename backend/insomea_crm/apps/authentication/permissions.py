from rest_framework import permissions

class BaseRolePermission(permissions.BasePermission):
    message = "Vous n'avez pas les permissions nécessaires."

class IsAdmin(BaseRolePermission):
    message = "Seuls les administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == 'ADMIN'
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)

class IsCommercial(BaseRolePermission):
    message = "Seuls les commerciaux peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role == 'COMMERCIAL'


class IsCommercialOrAdmin(BaseRolePermission):
    message = "Seuls les commerciaux et administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['COMMERCIAL', 'ADMIN']

class IsTechnicien(BaseRolePermission):
    message = "Seuls les techniciens peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role == 'TECHNICIEN'


class IsTechnicienOrAdmin(BaseRolePermission):
    message = "Seuls les techniciens et administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['TECHNICIEN', 'ADMIN']

class IsFinance(BaseRolePermission):
    message = "Seuls le service financier peut effectuer cette action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role == 'FINANCE'


class IsFinanceOrAdmin(BaseRolePermission):
    message = "Seuls le service financier et les administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['FINANCE', 'ADMIN']

class IsOwnerOrAdmin(BaseRolePermission):
    message = "Vous ne pouvez modifier que votre propre profil."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True

        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        if hasattr(obj, 'commercial'):
            return obj.commercial == request.user
        
        if isinstance(obj, type(request.user)):
            return obj == request.user
        
        return False
    
class IsAuthenticatedReadOnly(BaseRolePermission):
    message = "Vous avez un accès en lecture seule."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.method in permissions.SAFE_METHODS

class CommercialCanOnlyAccessOwnPaniers(BaseRolePermission):
    message = "Vous ne pouvez accéder qu'à vos propres paniers."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True
        
        if request.user.role == 'COMMERCIAL':
            return obj.commercial == request.user
        
        return False

def is_admin(user):
    return user and user.is_authenticated and user.role == 'ADMIN'


def is_commercial(user):
    return user and user.is_authenticated and user.role == 'COMMERCIAL'


def is_technicien(user):
    return user and user.is_authenticated and user.role == 'TECHNICIEN'


def is_finance(user):
    return user and user.is_authenticated and user.role == 'FINANCE'


def has_role(user, role):
    return user and user.is_authenticated and user.role == role


def has_any_role(user, roles):
    return user and user.is_authenticated and user.role in roles