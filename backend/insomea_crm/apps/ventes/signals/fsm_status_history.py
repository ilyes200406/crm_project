"""
SIGNALS - ventes

Auto logging des transitions FSM et notifications metier.
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django_fsm.signals import post_transition

from ..models import (
    Opportunity,
    OpportunityLine,
    OpportunityStatus,
    Provision,
    ProvisionStatus,
#    StatusHistory,
)

"""
@receiver(post_transition)
def log_fsm_transition(sender, instance, name, source, target, **kwargs):
    from ..models import Subscription

    if sender not in [Opportunity, OpportunityLine, Provision, Subscription]:
        return

    method_kwargs = kwargs.get('method_kwargs', {})
    user = method_kwargs.get('user')
    ip_address = method_kwargs.get('ip_address')

    history_data = {
        'status_precedent': source,
        'status_suivant': target,
        'transition_name': name,
        'changed_by': user,
        'ip_address': ip_address,
        'description': f"Transition FSM : {name}",
        'metadata': {
            'transition_name': name,
            'source': source,
            'target': target,
        },
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
"""

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


@receiver(post_delete, sender=OpportunityLine)
def update_opportunity_status_on_line_delete(sender, instance, **kwargs):
    """Recompute opportunity status after deleting a line."""
    from ..services.opportunity_service import update_opportunity_status_from_lines

    if instance.opportunity_id:
        try:
            update_opportunity_status_from_lines(instance.opportunity)
        except Opportunity.DoesNotExist:
            pass





# FSM transitions for SupplierQuoteLine, InsomeaQuote, and ClientPO are handled
# exclusively in their respective services (quote_service.py, purchase_order_service.py).
# Signals must not duplicate FSM transitions — services are the single source of truth.
