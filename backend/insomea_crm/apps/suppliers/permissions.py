"""
PERMISSIONS - APP SUPPLIERS

RBAC :
- ADMIN : Full CRUD
- FINANCE : Full CRUD
- COMMERCIAL : Read-only
- TECHNICIEN : Read-only
"""

from rest_framework import permissions


# ═══════════════════════════════════════════════════════════
# BASE PERMISSIONS
# ═══════════════════════════════════════════════════════════

class IsAuthenticated(permissions.BasePermission):
    """Vérifie que l'utilisateur est authentifié"""
    
    message = "Authentification requise."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


# ═══════════════════════════════════════════════════════════
# SUPPLIER PERMISSIONS
# ═══════════════════════════════════════════════════════════

class CanAccessSupplier(permissions.BasePermission):
    """
    Permission pour accès suppliers
    
    Règles :
    - ADMIN : Full CRUD
    - FINANCE : Full CRUD
    - COMMERCIAL : Read-only
    - TECHNICIEN : Read-only
    """
    
    message = "Vous n'avez pas accès aux fournisseurs."
    
    def has_permission(self, request, view):
        """Permission niveau vue (global)"""
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lecture : tous les rôles
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Écriture : ADMIN ou FINANCE seulement
        if request.user.role in ['ADMIN', 'FINANCE']:
            return True
        
        self.message = "Seuls les admins et finance peuvent modifier des fournisseurs."
        return False
    
    def has_object_permission(self, request, view, obj):
        """Permission niveau objet (spécifique)"""
        
        # Lecture : tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Écriture : ADMIN ou FINANCE
        if request.user.role in ['ADMIN', 'FINANCE']:
            return True
        
        self.message = "Seuls les admins et finance peuvent modifier ce fournisseur."
        return False


class CanManageSupplier(permissions.BasePermission):
    """
    Permission pour gestion supplier (CRUD)
    
    Plus stricte : ADMIN ou FINANCE seulement
    """
    
    message = "Vous ne pouvez pas gérer les fournisseurs."
    
    def has_permission(self, request, view):
        """Filtre global : ADMIN ou FINANCE"""
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'FINANCE']
        )
    
    def has_object_permission(self, request, view, obj):
        """Vérifie rôle"""
        return request.user.role in ['ADMIN', 'FINANCE']


# ═══════════════════════════════════════════════════════════
# ACTION-SPECIFIC PERMISSIONS
# ═══════════════════════════════════════════════════════════

class CanActivateSupplier(permissions.BasePermission):
    """
    Permission pour activer supplier
    
    Règle : ADMIN ou FINANCE
    """
    
    message = "Seuls les admins et finance peuvent activer des fournisseurs."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'FINANCE']
        )


class CanDeactivateSupplier(permissions.BasePermission):
    """
    Permission pour désactiver supplier
    
    Règle : ADMIN seulement
    """
    
    message = "Seuls les admins peuvent désactiver des fournisseurs."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'ADMIN'
        )


# ═══════════════════════════════════════════════════════════
# COMBINED PERMISSION
# ═══════════════════════════════════════════════════════════

class SupplierPermission(permissions.BasePermission):
    """
    Permission ALL-IN-ONE pour suppliers
    
    Règles complètes :
    GET /suppliers/ :
      - Tous les rôles authentifiés
    
    POST /suppliers/ :
      - ADMIN, FINANCE
    
    GET /suppliers/{id}/ :
      - Tous les rôles authentifiés
    
    PUT/PATCH /suppliers/{id}/ :
      - ADMIN, FINANCE
    
    DELETE /suppliers/{id}/ :
      - ADMIN seulement (désactivation)
    """
    
    def has_permission(self, request, view):
        """Permission vue globale"""
        
        if not request.user or not request.user.is_authenticated:
            self.message = "Authentification requise."
            return False
        
        # GET : tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # POST : ADMIN ou FINANCE
        if request.method == 'POST':
            if request.user.role in ['ADMIN', 'FINANCE']:
                return True
            self.message = "Seuls les admins et finance peuvent créer des fournisseurs."
            return False
        
        # PUT/PATCH : ADMIN ou FINANCE
        if request.method in ['PUT', 'PATCH']:
            if request.user.role in ['ADMIN', 'FINANCE']:
                return True
            self.message = "Seuls les admins et finance peuvent modifier des fournisseurs."
            return False
        
        # DELETE : ADMIN seulement
        if request.method == 'DELETE':
            if request.user.role == 'ADMIN':
                return True
            self.message = "Seuls les admins peuvent désactiver des fournisseurs."
            return False
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Permission objet spécifique"""
        
        # Admin : tout
        if request.user.role == 'ADMIN':
            return True
        
        # Finance : CRUD (sauf delete)
        if request.user.role == 'FINANCE':
            if request.method in permissions.SAFE_METHODS:
                return True
            if request.method in ['PUT', 'PATCH', 'POST']:
                return True
            # DELETE refusé pour FINANCE
            self.message = "Seuls les admins peuvent désactiver des fournisseurs."
            return False
        
        # Commercial/Tech : read-only
        if request.user.role in ['COMMERCIAL', 'TECHNICIEN']:
            if request.method in permissions.SAFE_METHODS:
                return True
            self.message = "Vous avez un accès en lecture seule."
            return False
        
        return False