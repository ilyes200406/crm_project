from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied

from ..models.opportunityLine import OpportunityLine

from ..validators import (
    validate_opportunity_line_data,
)

from ..selectors import (
    get_opportunity_by_id,
    get_line_by_id,
)

@transaction.atomic
def add_line_to_opportunity(*, opportunity_id, data: dict, user, ip_address=None):
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=False)
    
    if user.role not in ['ADMIN', 'COMMERCIAL']:
        raise PermissionDenied('Seuls les commerciaux peuvent ajouter des lignes')
    
    if user.role == 'COMMERCIAL':
        if opportunity.created_by != user and opportunity.assigned_to != user:
            raise PermissionDenied('Vous ne pouvez modifier que vos propres opportunités')
    
    if not opportunity.can_add_items():
        raise ValidationError(f'Impossible d\'ajouter des lignes. Statut : {opportunity.get_status_display()}')
    
    validate_opportunity_line_data(data, opportunity=opportunity)
    
    data['opportunity'] = opportunity
    
    line = OpportunityLine.objects.create(**data)
    
    return line


@transaction.atomic
def update_opportunity_line(*, line_id, data: dict, user, ip_address=None):
    line = get_line_by_id(line_id)
    opportunity = line.opportunity
    
    if user.role not in ['ADMIN', 'COMMERCIAL']:
        raise PermissionDenied('Seuls les commerciaux peuvent modifier des lignes')
    
    if user.role == 'COMMERCIAL':
        if opportunity.created_by != user and opportunity.assigned_to != user:
            raise PermissionDenied('Vous ne pouvez modifier que vos propres opportunités')
    
    if not opportunity.can_edit():
        raise ValidationError('L\'opportunité ne peut plus être modifiée')

    validate_opportunity_line_data(data, opportunity=opportunity, line=line)
    
    for field, value in data.items():
        setattr(line, field, value)
    
    line.save()
    
    return line


@transaction.atomic
def remove_line_from_opportunity(*, line_id, user, ip_address=None):
    line = get_line_by_id(line_id)
    opportunity = line.opportunity
    
    if user.role not in ['ADMIN', 'COMMERCIAL']:
        raise PermissionDenied('Seuls les commerciaux peuvent supprimer des lignes')
    
    if user.role == 'COMMERCIAL':
        if opportunity.created_by != user and opportunity.assigned_to != user:
            raise PermissionDenied('Vous ne pouvez modifier que vos propres opportunités')

    if not opportunity.can_edit():
        raise ValidationError('L\'opportunité ne peut plus être modifiée')
    
    line.delete()