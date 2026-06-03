"""
SIGNALS - ventes

Auto logging des transitions FSM et notifications metier.
"""

import threading

from django.db.models.signals import pre_delete, post_delete, post_save
from django.dispatch import receiver
from django_fsm.signals import post_transition

_deletion_context = threading.local()


def _opportunity_is_being_deleted(opportunity_id):
    return opportunity_id in getattr(_deletion_context, 'ids', set())

from ..models import (
    Opportunity,
    OpportunityLine,
    OpportunityStatus,
    Provision,
    ProvisionStatus,
    StatusHistory,
    Subscription,
    SubscriptionStatus,
)


@receiver(post_transition)
def log_fsm_transition(sender, instance, name, source, target, **kwargs):
    """Auto-log every FSM state transition into StatusHistory."""
    from ...core.current_user import get_current_user, get_current_ip

    if sender not in [Opportunity, OpportunityLine, Provision, Subscription]:
        return

    history_data = {
        'status_precedent': source or '',
        'status_suivant': target,
        'transition_name': name,
        'changed_by': get_current_user(),
        'ip_address': get_current_ip(),
        'description': f"Transition FSM : {name}",
        'metadata': {'transition_name': name, 'source': source, 'target': target},
    }

    if sender == OpportunityLine:
        history_data['opportunity_line'] = instance
    elif sender == Opportunity:
        history_data['opportunity'] = instance
    elif sender == Provision:
        history_data['provision'] = instance
    elif sender == Subscription:
        history_data['subscription'] = instance

    StatusHistory.objects.create(**history_data)


@receiver(post_save, sender=Opportunity)
def log_opportunity_created(sender, instance, created, **kwargs):
    """Audit log when an Opportunity is first created."""
    if not created:
        return
    from ...core.current_user import get_current_user, get_current_ip
    StatusHistory.objects.create(
        opportunity=instance,
        status_precedent='',
        status_suivant=instance.status,
        transition_name='create',
        changed_by=get_current_user(),
        ip_address=get_current_ip(),
        description="Opportunité créée",
        metadata={'reference': instance.reference, 'type': instance.type},
    )


@receiver(post_save, sender=OpportunityLine)
def log_opportunity_line_created(sender, instance, created, **kwargs):
    """Audit log when an OpportunityLine is first created."""
    if not created:
        return
    from ...core.current_user import get_current_user, get_current_ip
    StatusHistory.objects.create(
        opportunity_line=instance,
        status_precedent='',
        status_suivant=instance.status,
        transition_name='create',
        changed_by=get_current_user(),
        ip_address=get_current_ip(),
        description=f"Ligne ajoutée : {instance.product.title} x{instance.quantity}",
        metadata={
            'product_id': str(instance.product.id),
            'quantity': instance.quantity,
            'billing_cycle': instance.billing_cycle,
        },
    )


@receiver(post_save, sender=Provision)
def log_provision_created(sender, instance, created, **kwargs):
    """Audit log when a Provision is first created."""
    if not created:
        return
    from ...core.current_user import get_current_user, get_current_ip
    StatusHistory.objects.create(
        provision=instance,
        status_precedent='',
        status_suivant=instance.status,
        transition_name='create',
        changed_by=get_current_user(),
        ip_address=get_current_ip(),
        description=f"Provision créée ({'renouvellement' if instance.is_renewal else 'initiale'})",
        metadata={
            'opportunity_line_id': str(instance.opportunity_line_id),
            'product_title': instance.opportunity_line.product.title,
            'is_renewal': instance.is_renewal,
        },
    )


@receiver(post_transition, sender=Opportunity)
def notify_on_opportunity_transition(sender, instance, name, source, target, **kwargs):
    """Finance notification when client PO is received."""
    from ..notifications.services import notify_finance_to_approve

    if target == OpportunityStatus.CLIENT_PO_RECIEVED:
        notify_finance_to_approve(instance)


@receiver(post_save, sender=Provision)
def notify_on_provision_created(sender, instance, created, **kwargs):
    """Technician notification when a provision is created."""
    from ..notifications.services import notify_techniciens_provision_waiting

    if created and instance.status == ProvisionStatus.WAITING_PROVISION:
        notify_techniciens_provision_waiting(instance)


@receiver(post_transition, sender=Provision)
def notify_on_provision_transition(sender, instance, name, source, target, **kwargs):
    """Global notification when a provision completes."""
    from ..notifications.services import notify_all_provisioned

    if target == ProvisionStatus.PROVISIONED:
        notify_all_provisioned(instance)


@receiver(post_save, sender=OpportunityLine)
def update_opportunity_status_on_line_save(sender, instance, created, **kwargs):
    """Keep opportunity status in sync with line statuses."""
    from ..services.opportunity_service import update_opportunity_status_from_lines

    if getattr(instance, '_updating_opportunity_status', False):
        return

    instance._updating_opportunity_status = True
    update_opportunity_status_from_lines(instance.opportunity)
    delattr(instance, '_updating_opportunity_status')


@receiver(pre_delete, sender=Opportunity)
def mark_opportunity_deleting(sender, instance, **kwargs):
    """Flag this opportunity as being deleted so line signals can skip audit logging."""
    if not hasattr(_deletion_context, 'ids'):
        _deletion_context.ids = set()
    _deletion_context.ids.add(instance.id)


@receiver(post_delete, sender=Opportunity)
def unmark_opportunity_deleting(sender, instance, **kwargs):
    """Clean up the deletion flag after the opportunity is fully removed."""
    getattr(_deletion_context, 'ids', set()).discard(instance.id)


@receiver(post_delete, sender=OpportunityLine)
def handle_opportunity_line_deleted(sender, instance, **kwargs):
    """Recompute opportunity status and log deletion after a line is removed."""
    from ..services.opportunity_service import update_opportunity_status_from_lines
    from ...core.current_user import get_current_user, get_current_ip

    if not instance.opportunity_id:
        return

    # Opportunity is being cascade-deleted — skip logging to avoid deferred FK violation
    if _opportunity_is_being_deleted(instance.opportunity_id):
        return

    try:
        opp = Opportunity.objects.get(id=instance.opportunity_id)
        StatusHistory.objects.create(
            opportunity=opp,
            status_precedent=opp.status,
            status_suivant=opp.status,
            transition_name='line_deleted',
            changed_by=get_current_user(),
            ip_address=get_current_ip(),
            description=f"Ligne supprimée : {instance.product.title} x{instance.quantity}",
            metadata={
                'line_id': str(instance.id),
                'product_id': str(instance.product_id),
                'product_title': instance.product.title,
                'quantity': instance.quantity,
                'line_status': instance.status,
            },
        )
        update_opportunity_status_from_lines(opp)
    except Opportunity.DoesNotExist:
        pass


# FSM transitions for SupplierQuoteLine, InsomeaQuote, and ClientPO are handled
# exclusively in their respective services (quote_service.py, purchase_order_service.py).
# Signals must not duplicate FSM transitions — services are the single source of truth.
