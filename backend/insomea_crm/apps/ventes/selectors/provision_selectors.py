from django.db.models import Q
from django.shortcuts import get_object_or_404

from ..models import (Provision, ProvisionStatus)

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


def get_provision_by_id(provision_id, *, user=None):
    queryset = Provision.objects.select_related(
        'opportunity_line',
        'opportunity_line__opportunity',
        'opportunity_line__product',
        'provisionned_by',
    ).prefetch_related('subscription')
    
    if user and user.role == 'TECHNICIEN':
        queryset = queryset.filter(Q(provisionned_by=user) | Q(opportunity_line__opportunity__assigned_to=user))
    
    return get_object_or_404(queryset, id=provision_id)

def get_all_provisions(*, user=None):
    qs = Provision.objects.select_related(
        'opportunity_line',
        'opportunity_line__opportunity',
        'opportunity_line__product',
        'provisionned_by',
    ).prefetch_related('subscription')

    if user and user.role == 'TECHNICIEN':
        qs = qs.filter(
            Q(provisionned_by=user) |
            Q(opportunity_line__opportunity__assigned_to=user)
        )

    return qs.order_by('-created_at')