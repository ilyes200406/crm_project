from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone

from ..models.opportunity import Opportunity, OpportunityStatus
from ..models.opportunityLine import OpportunityLine, OpportunityLineStatus

from ..validators import (
    validate_opportunity_data,
    validate_opportunity_line_data,
    normalize_opportunity_name,
)

from ..selectors import (
    get_opportunity_by_id,
    get_line_by_id,
)

@transaction.atomic
def create_opportunity(*, data: dict, user, ip_address=None):
    if user.role not in ['ADMIN', 'COMMERCIAL']:
        raise PermissionDenied(
            'Seuls les admins et commerciaux peuvent créer des opportunités'
        )

    payload = data.copy()

    name = normalize_opportunity_name(payload.get('name'))
    if not name:
        raise ValidationError("Le nom de l'opportunité est requis")

    payload['name'] = name

    validate_opportunity_data(payload)

    payload['status'] = OpportunityStatus.DRAFT
    payload['created_by'] = user

    if user.role == 'COMMERCIAL' and not payload.get('assigned_to'):
        payload['assigned_to'] = user

    opportunity = Opportunity.objects.create(**payload)

    return opportunity


@transaction.atomic
def update_opportunity(*, opportunity_id, data: dict, user, ip_address=None):
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=False)
    
    if user.role == 'COMMERCIAL':
        if opportunity.created_by != user and opportunity.assigned_to != user:
            raise PermissionDenied('Vous ne pouvez modifier que vos propres opportunités')
    
    elif user.role in ['TECHNICIEN', 'FINANCE']:
        raise PermissionDenied('Vous n\'avez pas les permissions pour modifier cette opportunité')
    
    unrestricted_fields = {'notes', 'assigned_to'}
    restricted_fields = set(data.keys()) - unrestricted_fields
    
    if restricted_fields and not opportunity.can_edit():
        raise ValidationError(
            f'L\'opportunité {opportunity.reference} ne peut plus être modifiée. '
            f'Statut actuel : {opportunity.get_status_display()}'
        )

    validate_opportunity_data(data, opportunity=opportunity)
    
    for field, value in data.items():
        setattr(opportunity, field, value)
    
    opportunity.save()
    
    return opportunity


@transaction.atomic
def delete_opportunity(*, opportunity_id, user, ip_address=None):
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=True)
    
    if user.role == 'COMMERCIAL':
        if opportunity.created_by != user and opportunity.assigned_to != user:
            raise PermissionDenied('Vous ne pouvez supprimer que vos propres opportunités')
    elif user.role in ['TECHNICIEN', 'FINANCE']:
        raise PermissionDenied('Vous n\'avez pas les permissions pour supprimer des opportunités')
    
    if opportunity.status == OpportunityStatus.CANCELLED:
        raise ValidationError('L\'opportunité est déjà annulée')
    
    for line in opportunity.lines.all():
        if line.status != OpportunityLineStatus.CANCELLED:
            line.cancel(reason='Opportunité supprimée')
            line.save()

    opportunity.cancel(reason='Suppression via interface')
    opportunity.cancellation_reason = 'Suppression par utilisateur'
    opportunity.save()