"""
SUBSCRIPTION SELECTORS

Queries optimisées subscriptions
"""

from django.db.models import Q, Prefetch, F
from django.core.exceptions import PermissionDenied
from datetime import date, timedelta

from ..models import Subscription, SubscriptionStatus, SubscriptionTerm


# ═══════════════════════════════════════════════════════════
# GET QUERIES
# ═══════════════════════════════════════════════════════════

def get_all_subscriptions(*, user=None):
    """
    Get all subscriptions avec optimisations
    
    Args:
        user: User instance (pour RBAC)
    
    Returns:
        QuerySet[Subscription]
    
    RBAC:
        - ADMIN: all
        - COMMERCIAL: all (voir clients)
        - FINANCE: all
        - TECHNICIEN: all
    """
    
    qs = Subscription.objects.select_related(
        'client',
        'product',
    ).prefetch_related(
        'provisions',
        Prefetch(
            'terms',
            queryset=SubscriptionTerm.objects.select_related(
                'opportunity',
                'provision'
            ).order_by('term_number')
        )
    )
    
    # RBAC filtering (si nécessaire)
    # Pour l'instant: tous les rôles voient toutes subscriptions
    
    return qs


def get_subscription_by_id(subscription_id, *, user=None):
    """
    Get subscription by ID
    
    Args:
        subscription_id: UUID
        user: User instance
    
    Returns:
        Subscription
    
    Raises:
        Subscription.DoesNotExist
        PermissionDenied
    """
    
    subscription = get_all_subscriptions(user=user).get(id=subscription_id)
    
    return subscription


def get_subscription_by_number(subscription_number, *, user=None):
    """
    Get subscription by Microsoft subscription number
    
    Args:
        subscription_number: str
        user: User instance
    
    Returns:
        Subscription
    
    Raises:
        Subscription.DoesNotExist
    """
    
    return get_all_subscriptions(user=user).get(
        subscription_number=subscription_number
    )


# ═══════════════════════════════════════════════════════════
# FILTERED QUERIES
# ═══════════════════════════════════════════════════════════

def get_active_subscriptions(*, user=None):
    """
    Get active subscriptions
    
    Returns:
        QuerySet[Subscription] status=ACTIVE
    """
    
    return get_all_subscriptions(user=user).filter(
        status=SubscriptionStatus.ACTIVE
    )


def get_pending_renewal_subscriptions(*, user=None):
    """
    Get subscriptions pending renewal
    
    Returns:
        QuerySet[Subscription] status=PENDING_RENEWAL
    """
    
    return get_all_subscriptions(user=user).filter(
        status=SubscriptionStatus.PENDING_RENEWAL
    )


def get_expired_subscriptions(*, user=None):
    """
    Get expired subscriptions
    
    Returns:
        QuerySet[Subscription] status=EXPIRED
    """
    
    return get_all_subscriptions(user=user).filter(
        status=SubscriptionStatus.EXPIRED
    )


def get_expiring_subscriptions(*, days=30, user=None):
    """
    Get subscriptions expiring in X days
    
    Args:
        days: int nombre jours
        user: User instance
    
    Returns:
        QuerySet[Subscription] expirant dans X jours
    """
    
    threshold_date = date.today() + timedelta(days=days)
    
    return get_active_subscriptions(user=user).filter(
        current_term_end__lte=threshold_date,
        current_term_end__gte=date.today()
    ).order_by('current_term_end')


def get_subscriptions_by_client(client_id, *, user=None):
    """
    Get subscriptions par client
    
    Args:
        client_id: UUID
        user: User instance
    
    Returns:
        QuerySet[Subscription]
    """
    
    return get_all_subscriptions(user=user).filter(client_id=client_id)


def get_subscriptions_by_product(product_id, *, user=None):
    """
    Get subscriptions par produit
    
    Args:
        product_id: UUID
        user: User instance
    
    Returns:
        QuerySet[Subscription]
    """
    
    return get_all_subscriptions(user=user).filter(product_id=product_id)


def get_subscriptions_needing_renewal(*, days_threshold=30, user=None):
    """
    Get subscriptions nécessitant renewal (PENDING_RENEWAL sans renewal en cours)
    
    Args:
        days_threshold: int
        user: User instance
    
    Returns:
        QuerySet[Subscription]
    
    Note:
        Exclut celles avec renewal déjà en cours
    """
    
    from ..services.renewal_service import get_subscriptions_needing_renewal
    
    return get_subscriptions_needing_renewal(
        user=user,
        days_threshold=days_threshold
    )


# ═══════════════════════════════════════════════════════════
# STATS / ANALYTICS
# ═══════════════════════════════════════════════════════════

def get_subscription_stats(*, user=None):
    """
    Get stats globales subscriptions
    
    Returns:
        dict {
            'total': int,
            'active': int,
            'pending_renewal': int,
            'expired': int,
            'expiring_30d': int,
            'expiring_7d': int,
        }
    """
    
    qs = get_all_subscriptions(user=user)
    
    return {
        'total': qs.count(),
        'active': qs.filter(status=SubscriptionStatus.ACTIVE).count(),
        'pending_renewal': qs.filter(status=SubscriptionStatus.PENDING_RENEWAL).count(),
        'expired': qs.filter(status=SubscriptionStatus.EXPIRED).count(),
        'expiring_30d': get_expiring_subscriptions(days=30, user=user).count(),
        'expiring_7d': get_expiring_subscriptions(days=7, user=user).count(),
    }