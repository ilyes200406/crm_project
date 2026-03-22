from django.db.models import Q
from django.shortcuts import get_object_or_404
from datetime import timedelta
from django.utils import timezone

from ..models import (Provision, ProvisionStatus, Subscription)

def get_provisions_waiting(user=None):
    queryset = Provision.objects.filter(
        status=ProvisionStatus.WAITING_PROVISION
    ).select_related(
        'opportunity_line',
        'opportunity_line__opportunity',
        'opportunity_line__opportunity__client',
        'opportunity_line__product',
    )
    
    # RBAC
    if user and user.role == 'TECHNICIEN':
        queryset = queryset.filter(
            Q(provisionned_by=user) |
            Q(opportunity_line__opportunity__assigned_to=user)
        )
    
    return queryset.order_by('opportunity_line__created_at')


def get_provisions_in_progress(user=None):
    queryset = Provision.objects.filter(
        status=ProvisionStatus.PROVISIONING
    ).select_related(
        'opportunity_line',
        'opportunity_line__opportunity',
        'opportunity_line__opportunity__client',
        'opportunity_line__product',
        'provisionned_by',
    )
    
    # RBAC
    if user and user.role == 'TECHNICIEN':
        queryset = queryset.filter(provisionned_by=user)
    
    return queryset.order_by('provisioning_started_at')


def get_provision_by_id(provision_id):
    return get_object_or_404(
        Provision.objects.select_related(
            'opportunity_line',
            'opportunity_line__opportunity',
            'opportunity_line__product',
            'provisionned_by',
        ).prefetch_related(
            'subscription',
        ),
        id=provision_id
    )


# ═══════════════════════════════════════════════════════════
# SUBSCRIPTION SELECTORS
# ═══════════════════════════════════════════════════════════

def get_active_subscriptions(user=None):
    """
    Récupère subscriptions actives
    
    Args:
        user: User instance (RBAC)
    
    Returns:
        QuerySet Subscription
    """
    queryset = Subscription.objects.select_related(
        'provision',
        'provision__opportunity_line',
        'provision__opportunity_line__opportunity',
        'provision__opportunity_line__opportunity__client',
        'provision__opportunity_line__product',
    ).order_by('end_date')
    
    # RBAC
    if user and user.role == 'COMMERCIAL':
        queryset = queryset.filter(
            Q(provision__opportunity_line__opportunity__created_by=user) |
            Q(provision__opportunity_line__opportunity__assigned_to=user)
        )
    
    return queryset


def get_expiring_subscriptions(days=30, user=None):
    """
    Récupère subscriptions expirant dans X jours
    
    Args:
        days: int nombre de jours
        user: User instance (RBAC)
    
    Returns:
        QuerySet Subscription
    """
    end_date_threshold = timezone.now().date() + timedelta(days=days)
    
    return get_active_subscriptions(user=user).filter(
        end_date__lte=end_date_threshold,
        end_date__gte=timezone.now().date()
    )


def get_subscription_by_id(subscription_id):
    """
    Récupère subscription par ID
    
    Args:
        subscription_id: UUID
    
    Returns:
        Subscription instance
    
    Raises:
        Http404: Si n'existe pas
    """
    return get_object_or_404(
        Subscription.objects.select_related(
            'provision',
            'provision__opportunity_line',
            'provision__opportunity_line__opportunity',
            'provision__opportunity_line__product',
        ),
        id=subscription_id
    )


def get_subscription_by_microsoft_id(microsoft_subscription_id):
    """
    Récupère subscription par ID Microsoft
    
    Args:
        microsoft_subscription_id: str
    
    Returns:
        Subscription instance ou None
    """
    try:
        return Subscription.objects.select_related(
            'provision',
            'provision__opportunity_line',
            'provision__opportunity_line__opportunity',
            'provision__opportunity_line__product',
        ).get(subscription_number=microsoft_subscription_id)
    except Subscription.DoesNotExist:
        return None