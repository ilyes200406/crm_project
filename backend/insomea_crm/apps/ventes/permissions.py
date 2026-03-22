"""
PERMISSIONS - APP OPPORTUNITIES

Custom permissions RBAC
"""

from rest_framework import permissions


class IsCommercialOrAdmin(permissions.BasePermission):
    """
    Permission: Seuls COMMERCIAL ou ADMIN
    
    Usage:
        - Créer devis fournisseur
        - Créer devis Insomea
        - Upload BC client
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['ADMIN', 'COMMERCIAL']
        )


class IsTechnicienOrAdmin(permissions.BasePermission):
    """
    Permission: Seuls TECHNICIEN ou ADMIN
    
    Usage:
        - Actions provisioning (start, complete, fail)
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['ADMIN', 'TECHNICIEN']
        )


class IsFinanceOrAdmin(permissions.BasePermission):
    """
    Permission: Seuls FINANCE ou ADMIN
    
    Usage:
        - Approuver opportunités
        - Créer InsomeaPOs
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['ADMIN', 'FINANCE']
        )


class IsOpportunityOwnerOrAdmin(permissions.BasePermission):
    """
    Permission: Propriétaire opportunité ou ADMIN
    
    Usage:
        - Update/Delete opportunity
        - Update/Delete opportunity line
    
    Vérifie:
        - created_by = user OU
        - assigned_to = user OU
        - role = ADMIN
    """
    
    def has_object_permission(self, request, view, obj):
        # ADMIN passe toujours
        if request.user.role == 'ADMIN':
            return True
        
        # Détermine opportunity selon type objet
        from .models import Opportunity, OpportunityLine
        
        if isinstance(obj, Opportunity):
            opportunity = obj
        elif isinstance(obj, OpportunityLine):
            opportunity = obj.opportunity
        else:
            # Autres objets: deny par défaut
            return False
        
        # Vérifie ownership
        return (
            opportunity.created_by == request.user or
            opportunity.assigned_to == request.user
        )


class CanViewOpportunity(permissions.BasePermission):
    """
    Permission: Peut voir opportunité selon rôle
    
    Règles:
        - ADMIN: tout
        - COMMERCIAL: ses opportunités (created_by ou assigned_to)
        - FINANCE: opportunités CLIENT_PO_RECEIVED ou APPROVED
        - TECHNICIEN: opportunités APPROVED
    """
    
    def has_object_permission(self, request, view, obj):
        from .models import Opportunity, OpportunityStatus
        
        # Détermine opportunity
        if isinstance(obj, Opportunity):
            opportunity = obj
        elif hasattr(obj, 'opportunity'):
            opportunity = obj.opportunity
        elif hasattr(obj, 'opportunity_line'):
            opportunity = obj.opportunity_line.opportunity
        else:
            return False
        
        user = request.user
        
        # ADMIN: tout
        if user.role == 'ADMIN':
            return True
        
        # COMMERCIAL: ownership
        if user.role == 'COMMERCIAL':
            return (
                opportunity.created_by == user or
                opportunity.assigned_to == user
            )
        
        # FINANCE: phase avancée
        if user.role == 'FINANCE':
            return opportunity.status in [
                OpportunityStatus.CLIENT_PO_RECIEVED,
                OpportunityStatus.APPROUVED,
            ]
        
        # TECHNICIEN: APPROVED
        if user.role == 'TECHNICIEN':
            return opportunity.status == OpportunityStatus.APPROUVED
        
        return False