"""PERMISSIONS - APP PRODUCTS"""

from rest_framework import permissions


class ProductPermission(permissions.BasePermission):
    """
    Permissions products
    
    - ADMIN : Full CRUD
    - FINANCE : Read + utilisation dans opportunities
    - COMMERCIAL : Read + utilisation dans opportunities
    - TECHNICIEN : Read-only
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lecture : tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Écriture : ADMIN seulement
        if request.user.role_id == 'ADMIN':
            return True
        
        self.message = "Seuls les admins peuvent modifier le catalogue produits."
        return False