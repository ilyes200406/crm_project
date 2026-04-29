"""
EXPLICATION :

Permissions = RBAC (Role-Based Access Control)

Architecture :
- Custom DRF permission classes
- Intégration avec système auth existant
- Granularité fine (vue + objet)
- Messages d'erreur clairs

Niveaux de permission :
1. View-level : has_permission() - accès global à l'endpoint
2. Object-level : has_object_permission() - accès à un objet spécifique

Règles métier :
- ADMIN : Full access (CRUD complet)
- COMMERCIAL : CRUD sur ses clients assignés seulement
- FINANCE : Read-only (tous les clients)
- TECHNICIEN : Read-only (tous les clients)

Performance :
- Permissions évaluées AVANT queries
- Évite requêtes inutiles si 403
"""

from rest_framework import permissions
from django.core.exceptions import ObjectDoesNotExist


# ═══════════════════════════════════════════════════════════
# BASE PERMISSIONS
# ═══════════════════════════════════════════════════════════

class IsAuthenticated(permissions.BasePermission):
    """
    Vérifie que l'utilisateur est authentifié
    
    Explication :
    Requis pour TOUS les endpoints clients
    User anonyme → 401 Unauthorized
    
    Note :
    DRF a déjà IsAuthenticated built-in
    Celle-ci est custom pour messages personnalisés
    """
    
    message = "Authentification requise."
    
    def has_permission(self, request, view):
        """
        Vérifie JWT token valide
        
        Explication :
        request.user existe si JWT valide
        request.user.is_authenticated = True
        """
        return bool(request.user and request.user.is_authenticated)


# ═══════════════════════════════════════════════════════════
# ROLE-BASED PERMISSIONS
# ═══════════════════════════════════════════════════════════

class IsAdmin(permissions.BasePermission):
    """
    Seuls les ADMIN peuvent accéder
    
    Utilisation :
    Endpoints réservés admin uniquement
    Ex: soft delete, restore, bulk operations
    """
    
    message = "Seuls les administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        """Vérifie role ADMIN"""
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role_id == 'ADMIN'
        )


class IsCommercialOrAdmin(permissions.BasePermission):
    """
    COMMERCIAL ou ADMIN peuvent accéder
    
    Utilisation :
    Création clients, modification
    """
    
    message = "Seuls les commerciaux et administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        """Vérifie role COMMERCIAL ou ADMIN"""
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role_id in ['COMMERCIAL', 'ADMIN']
        )


class IsReadOnly(permissions.BasePermission):
    """
    Accès lecture seule pour méthodes SAFE
    
    Explication :
    SAFE_METHODS = GET, HEAD, OPTIONS
    → Lecture seulement
    
    POST, PUT, PATCH, DELETE → Refusé
    
    Utilisation :
    TECHNICIEN et FINANCE (read-only)
    """
    
    message = "Vous avez un accès en lecture seule."
    
    def has_permission(self, request, view):
        """Autorise seulement méthodes SAFE"""
        return request.method in permissions.SAFE_METHODS
        # Explication :
        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
        # GET /clients/ → True
        # POST /clients/ → False


# ═══════════════════════════════════════════════════════════
# CLIENT-SPECIFIC PERMISSIONS
# ═══════════════════════════════════════════════════════════

class CanAccessClient(permissions.BasePermission):
    """
    Permission complexe pour accès client
    
    Règles :
    - ADMIN : Accès complet à tous les clients
    - COMMERCIAL : Accès complet à SES clients assignés seulement
    - FINANCE : Read-only tous les clients
    - TECHNICIEN : Read-only tous les clients
    
    Explication :
    Permission hybride : vue + objet
    - has_permission() : Filtre global
    - has_object_permission() : Vérifie ownership
    """
    
    message = "Vous n'avez pas accès à ce client."
    
    def has_permission(self, request, view):
        """
        Permission niveau vue (global)
        
        Explication :
        Appelé AVANT get_queryset()
        Filtre accès global à l'endpoint
        
        Règles :
        - GET : Tous les rôles authentifiés
        - POST/PUT/PATCH/DELETE : ADMIN ou COMMERCIAL seulement
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lecture : tous les rôles
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Écriture : ADMIN ou COMMERCIAL seulement
        return request.user.role_id in ['ADMIN', 'COMMERCIAL']
    
    def has_object_permission(self, request, view, obj):
        """
        Permission niveau objet (spécifique)
        
        Args:
            obj: Instance Client
        
        Explication :
        Appelé pour actions sur UN client spécifique
        - GET /clients/{id}/
        - PUT /clients/{id}/
        - DELETE /clients/{id}/
        
        Flow :
        1. has_permission() → True
        2. get_object() → récupère client
        3. has_object_permission() → vérifie ownership
        4. Si False → 403 Forbidden
        """
        
        # Admin : accès complet
        if request.user.role_id == 'ADMIN':
            return True
        
        # Commercial : seulement ses clients
        if request.user.role_id == 'COMMERCIAL':
            # Lecture : peut voir ses clients
            if request.method in permissions.SAFE_METHODS:
                return obj.assigned_to == request.user
            
            # Écriture : peut modifier ses clients
            return obj.assigned_to == request.user
        
        # Finance/Tech : read-only
        if request.user.role_id in ['FINANCE', 'TECHNICIEN']:
            return request.method in permissions.SAFE_METHODS
        
        # Autres rôles : refusé
        return False


class CanManageClient(permissions.BasePermission):
    """
    Permission pour gestion client (CRUD)
    
    Différence avec CanAccessClient :
    Plus stricte → seulement CRUD complet
    
    Règles :
    - ADMIN : Full CRUD tous les clients
    - COMMERCIAL : Full CRUD SES clients
    - Autres : Refusé
    
    Utilisation :
    Actions critiques (delete, assign, etc.)
    """
    
    message = "Vous ne pouvez pas gérer ce client."
    
    def has_permission(self, request, view):
        """
        Filtre global
        
        Explication :
        Seulement ADMIN ou COMMERCIAL
        Autres rôles → 403 immédiat
        """
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role_id in ['ADMIN', 'COMMERCIAL']
        )
    
    def has_object_permission(self, request, view, obj):
        """
        Vérifie ownership
        
        Explication :
        ADMIN : tout
        COMMERCIAL : ses clients seulement
        """
        if request.user.role_id == 'ADMIN':
            return True
        
        if request.user.role_id == 'COMMERCIAL':
            return obj.assigned_to == request.user
        
        return False


# ═══════════════════════════════════════════════════════════
# CONTACT PERMISSIONS
# ═══════════════════════════════════════════════════════════

class CanManageContact(permissions.BasePermission):
    """
    Permission pour gestion contacts
    
    Règles :
    Même que client parent
    - ADMIN : tous les contacts
    - COMMERCIAL : contacts de SES clients
    - Autres : read-only
    
    Explication :
    Contact hérite permissions du client
    """
    
    message = "Vous ne pouvez pas gérer ce contact."
    
    def has_permission(self, request, view):
        """Filtre global"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lecture : tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Écriture : ADMIN ou COMMERCIAL
        return request.user.role_id in ['ADMIN', 'COMMERCIAL']
    
    def has_object_permission(self, request, view, obj):
        """
        Vérifie via client parent
        
        Args:
            obj: Instance Contact
        
        Explication :
        Contact.client = Client instance
        Vérifie permission sur client
        """
        
        # Admin : tout
        if request.user.role_id == 'ADMIN':
            return True
        
        # Commercial : contacts de ses clients
        if request.user.role_id == 'COMMERCIAL':
            if request.method in permissions.SAFE_METHODS:
                return obj.client.assigned_to == request.user
            return obj.client.assigned_to == request.user
        
        # Finance/Tech : read-only
        if request.user.role_id in ['FINANCE', 'TECHNICIEN']:
            return request.method in permissions.SAFE_METHODS
        
        return False


# ═══════════════════════════════════════════════════════════
# ACTIVITY PERMISSIONS
# ═══════════════════════════════════════════════════════════

class CanViewActivity(permissions.BasePermission):
    """
    Permission pour voir activités client
    
    Règles :
    Read-only basé sur accès client parent
    
    Explication :
    Activités = read-only pour tous
    Créées automatiquement par système
    """
    
    message = "Vous ne pouvez pas voir ces activités."
    
    def has_permission(self, request, view):
        """
        Seulement méthodes SAFE
        
        Explication :
        Activités jamais modifiées manuellement
        Création via services.log_client_activity()
        """
        return (
            request.user and 
            request.user.is_authenticated and 
            request.method in permissions.SAFE_METHODS
        )
    
    def has_object_permission(self, request, view, obj):
        """
        Vérifie via client parent
        
        Args:
            obj: Instance ClientActivity
        """
        
        # Admin : tout
        if request.user.role_id == 'ADMIN':
            return True
        
        # Commercial : activités de ses clients
        if request.user.role_id == 'COMMERCIAL':
            return obj.client.assigned_to == request.user
        
        # Finance/Tech : toutes les activités
        if request.user.role_id in ['FINANCE', 'TECHNICIEN']:
            return True
        
        return False


# ═══════════════════════════════════════════════════════════
# COMBINED PERMISSIONS
# ═══════════════════════════════════════════════════════════

class ClientPermission(permissions.BasePermission):
    """
    Permission ALL-IN-ONE pour clients
    
    Combine toutes les règles en une seule classe
    Utilisable directement dans ViewSets
    
    Explication :
    Permission la plus utilisée
    Couvre tous les cas d'usage
    
    Règles complètes :
    GET /clients/ :
      - ADMIN : Tous
      - COMMERCIAL : Ses clients
      - FINANCE/TECH : Tous (read-only)
    
    POST /clients/ :
      - ADMIN : OK
      - COMMERCIAL : OK (auto-assigné)
      - Autres : 403
    
    GET /clients/{id}/ :
      - ADMIN : Tous
      - COMMERCIAL : Ses clients
      - FINANCE/TECH : Tous
    
    PUT/PATCH /clients/{id}/ :
      - ADMIN : Tous
      - COMMERCIAL : Ses clients
      - Autres : 403
    
    DELETE /clients/{id}/ :
      - ADMIN seulement
    """
    
    def has_permission(self, request, view):
        """
        Permission vue globale
        
        Explication :
        Filtre accès endpoint selon action
        """
        if not request.user or not request.user.is_authenticated:
            self.message = "Authentification requise."
            return False
        
        # GET : tous les rôles
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # POST : ADMIN ou COMMERCIAL
        if request.method == 'POST':
            if request.user.role_id in ['ADMIN', 'COMMERCIAL']:
                return True
            self.message = "Seuls les administrateurs et commerciaux peuvent créer des clients."
            return False
        
        # PUT/PATCH : ADMIN ou COMMERCIAL
        if request.method in ['PUT', 'PATCH']:
            if request.user.role_id in ['ADMIN', 'COMMERCIAL']:
                return True
            self.message = "Seuls les administrateurs et commerciaux peuvent modifier des clients."
            return False
        
        # DELETE : ADMIN seulement
        if request.method == 'DELETE':
            if request.user.role_id == 'ADMIN':
                return True
            self.message = "Seuls les administrateurs peuvent désactiver des clients."
            return False
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Permission objet spécifique
        
        Args:
            obj: Client instance
        """
        
        # Admin : accès complet
        if request.user.role_id == 'ADMIN':
            return True
        
        # Commercial : ses clients seulement
        if request.user.role_id == 'COMMERCIAL':
            if obj.assigned_to == request.user:
                return True
            self.message = "Vous ne pouvez accéder qu'à vos propres clients."
            return False
        
        # Finance/Tech : read-only
        if request.user.role_id in ['FINANCE', 'TECHNICIEN']:
            if request.method in permissions.SAFE_METHODS:
                return True
            self.message = "Vous avez un accès en lecture seule."
            return False
        
        return False


# ═══════════════════════════════════════════════════════════
# PERMISSION HELPERS
# ═══════════════════════════════════════════════════════════

def user_can_access_client(user, client):
    """
    Helper function pour vérifier accès client
    
    Args:
        user: Utilisateur
        client: Client instance
    
    Returns:
        bool
    
    Utilisation :
    Dans services, views pour checks manuels
    
    Exemple :
    if not user_can_access_client(request.user, client):
        raise PermissionDenied()
    """
    
    if not user or not user.is_authenticated:
        return False
    
    if user.role_id == 'ADMIN':
        return True
    
    if user.role_id == 'COMMERCIAL':
        return client.assigned_to == user
    
    if user.role_id in ['FINANCE', 'TECHNICIEN']:
        return True  # Read-only access
    
    return False


def user_can_modify_client(user, client):
    """
    Helper pour vérifier permission modification
    
    Returns:
        bool
    
    Explication :
    Plus strict que user_can_access_client
    Seulement ADMIN ou commercial owner
    """
    
    if not user or not user.is_authenticated:
        return False
    
    if user.role_id == 'ADMIN':
        return True
    
    if user.role_id == 'COMMERCIAL':
        return client.assigned_to == user
    
    return False


def get_accessible_clients_queryset(user, base_queryset=None):
    """
    Retourne queryset filtré selon permissions user
    
    Args:
        user: Utilisateur
        base_queryset: QuerySet de base (optionnel)
    
    Returns:
        QuerySet filtré
    
    Explication :
    Applique filtres RBAC automatiquement
    Évite expose de données non autorisées
    
    Utilisation :
    Dans views pour filtrage automatique
    
    Exemple :
    queryset = get_accessible_clients_queryset(request.user)
    """
    
    from .models import Client
    
    if base_queryset is None:
        base_queryset = Client.objects.all()
    
    # Admin : tout
    if user.role_id == 'ADMIN':
        return base_queryset
    
    # Commercial : ses clients
    if user.role_id == 'COMMERCIAL':
        return base_queryset.filter(assigned_to=user)
    
    # Finance/Tech : tous (pour read-only)
    if user.role_id in ['FINANCE', 'TECHNICIEN']:
        return base_queryset.filter(is_active=True)
    
    # Autre : vide
    return base_queryset.none()


# ═══════════════════════════════════════════════════════════
# ACTION-SPECIFIC PERMISSIONS
# ═══════════════════════════════════════════════════════════

class CanAssignClient(permissions.BasePermission):
    """
    Permission pour réassigner un client
    
    Règle :
    ADMIN seulement
    
    Explication :
    Réassignation = action critique
    Change responsabilité client
    Réservée aux admins
    """
    
    message = "Seuls les administrateurs peuvent réassigner des clients."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role_id == 'ADMIN'
        )


class CanBulkUpdate(permissions.BasePermission):
    """
    Permission pour opérations en masse
    
    Règle :
    ADMIN seulement
    
    Explication :
    Bulk operations = puissantes et dangereuses
    Réservées aux admins
    
    Exemples :
    - Bulk delete
    - Bulk status change
    - Bulk assign
    """
    
    message = "Seuls les administrateurs peuvent effectuer des opérations en masse."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role_id == 'ADMIN'
        )


class CanExportData(permissions.BasePermission):
    """
    Permission pour export données
    
    Règles :
    - ADMIN : Export complet
    - COMMERCIAL : Export ses clients
    - FINANCE : Export tous les clients
    - TECH : Refusé
    
    Explication :
    Export = exposition potentielle données sensibles
    Contrôle strict
    """
    
    message = "Vous n'avez pas les permissions pour exporter des données."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role_id in ['ADMIN', 'COMMERCIAL', 'FINANCE']
        )