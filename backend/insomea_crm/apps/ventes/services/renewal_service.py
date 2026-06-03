"""
RENEWAL SERVICE

Business logic création opportunités renewal:
- Création automatique opportunité renewal
- Préparation données depuis subscription
"""

from django.db import transaction
from django.core.exceptions import ValidationError

from ..models import (
    Opportunity,
    OpportunityLine,
    OpportunityType,
    OpportunityStatus,
    SubscriptionStatus,
)


# ═══════════════════════════════════════════════════════════
# CRÉATION RENEWAL OPPORTUNITY
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def create_renewal_opportunity(*, subscription, user, quantity=None, notes='', ip_address=None):
    """
    Crée opportunité renewal pour subscription
    
    Args:
        subscription: Subscription instance
        user: User instance (COMMERCIAL)
        ip_address: str
    
    Returns:
        dict {
            'opportunity': Opportunity (RENEWAL),
            'line': OpportunityLine,
        }
    
    Raises:
        ValidationError: Si préconditions non remplies
    
    Business Rules:
        - Subscription doit être PENDING_RENEWAL
        - Crée Opportunity (type=RENEWAL)
        - Link related_opportunity → original opportunity
        - Crée OpportunityLine (renewal_of_subscription)
        - Pré-remplit: product, quantity, billing_cycle
        - Status: DRAFT
    
    Called by:
        - API endpoint (Commercial action)
        - Dashboard "Créer renouvellement"
    """
    
    # ───────────────────────────────────────────────────────
    # 1. VALIDATION
    # ───────────────────────────────────────────────────────
    
    if subscription.status not in [SubscriptionStatus.PENDING_RENEWAL, SubscriptionStatus.EXPIRED]:
        raise ValidationError(
            f'Un renouvellement ne peut être créé que pour une subscription en attente ou expirée. '
            f'Status actuel : {subscription.get_status_display()}'
        )
    
    # Vérifie pas déjà en cours renewal
    existing_renewal = OpportunityLine.objects.filter(
        renewal_of_subscription=subscription,
        opportunity__status__in=[
            OpportunityStatus.DRAFT,
            OpportunityStatus.SUPPLIER_QUOTE_REQUEST,
            OpportunityStatus.SUPPLIER_QUOTE_RECIEVED,
            OpportunityStatus.INSOMEA_QUOTE_CREATED,
            OpportunityStatus.CLIENT_PO_REQUEST,
            OpportunityStatus.CLIENT_PO_RECIEVED,
        ]
    ).exists()
    
    if existing_renewal:
        raise ValidationError(
            'Un renouvellement est déjà en cours pour cette subscription'
        )
    
    # ───────────────────────────────────────────────────────
    # 2. RÉCUPÈRE OPPORTUNITÉ ORIGINALE
    # ───────────────────────────────────────────────────────
    
    # Get original opportunity (Term 1)
    first_term = subscription.terms.filter(term_number=1).first()
    
    if not first_term:
        raise ValidationError('Subscription sans Term 1 (données corrompues)')
    
    original_opportunity = first_term.opportunity
    
    # ───────────────────────────────────────────────────────
    # 3. CRÉATION OPPORTUNITY RENEWAL
    # ───────────────────────────────────────────────────────

    final_quantity = quantity or subscription.quantity
    final_notes = notes or f"Renouvellement subscription {subscription.subscription_number}"

    renewal_opportunity = Opportunity.objects.create(
        type=OpportunityType.RENEWAL,
        related_opportunity=original_opportunity,
        name=f"Renouvellement {subscription.product.title} - {subscription.client.company_name}",
        client=subscription.client,
        created_by=user,
        assigned_to=original_opportunity.assigned_to or user,
        status=OpportunityStatus.DRAFT,
        notes=final_notes,
    )
    # reference auto-généré dans save()
    
    # ───────────────────────────────────────────────────────
    # 4. CRÉATION OPPORTUNITY LINE
    # ───────────────────────────────────────────────────────

    renewal_line = OpportunityLine.objects.create(
        opportunity=renewal_opportunity,
        product=subscription.product,
        quantity=final_quantity,
        billing_cycle=subscription.billing_cycle,
        renewal_of_subscription=subscription,
        notes=final_notes,
    )
    
    return {
        'opportunity': renewal_opportunity,
        'line': renewal_line,
    }


# ═══════════════════════════════════════════════════════════
# HELPERS RENEWAL
# ═══════════════════════════════════════════════════════════

def prepare_renewal_data_from_subscription(subscription):
    """
    Prépare données pour renewal depuis subscription
    
    Args:
        subscription: Subscription instance
    
    Returns:
        dict données pré-remplies
    
    Usage:
        Frontend peut appeler pour pré-remplir formulaire renewal
    """
    
    # Get latest term pricing
    latest_term = subscription.get_latest_term()
    
    if not latest_term:
        raise ValidationError('Subscription sans terme (données corrompues)')
    
    # Get original opportunity
    first_term = subscription.terms.filter(term_number=1).first()
    original_opportunity = first_term.opportunity if first_term else None
    
    return {
        'subscription_id': str(subscription.id),
        'subscription_number': subscription.subscription_number,
        'client_id': str(subscription.client.id),
        'client_name': subscription.client.company_name,
        'product_id': str(subscription.product.id),
        'product_name': subscription.product.title,
        'quantity': subscription.quantity,
        'billing_cycle': subscription.billing_cycle,
        'current_term_end': subscription.current_term_end,
        'days_until_expiration': subscription.days_until_expiration(),
        'last_unit_price_purchase': latest_term.unit_price_purchase,
        'last_unit_price_sale': latest_term.unit_price_sale,
        'original_opportunity_id': str(original_opportunity.id) if original_opportunity else None,
        'original_opportunity_reference': original_opportunity.reference if original_opportunity else None,
        'auto_renew': subscription.auto_renew,
    }


def get_subscriptions_needing_renewal(user=None, days_threshold=30):
    """
    Récupère subscriptions nécessitant renewal
    
    Args:
        user: User instance (RBAC)
        days_threshold: int jours avant expiration
    
    Returns:
        QuerySet[Subscription]
    
    Usage:
        Dashboard commercial "Renouvellements à traiter"
    """
    from ..selectors import get_active_subscriptions
    from datetime import date, timedelta
    
    threshold_date = date.today() + timedelta(days=days_threshold)
    
    subscriptions = get_active_subscriptions(user=user).filter(
        status=SubscriptionStatus.PENDING_RENEWAL,
        current_term_end__lte=threshold_date,
    )
    
    # Exclut celles avec renewal déjà en cours
    subscriptions = subscriptions.exclude(
        renewal_lines__opportunity__status__in=[
            OpportunityStatus.DRAFT,
            OpportunityStatus.SUPPLIER_QUOTE_REQUEST,
            OpportunityStatus.SUPPLIER_QUOTE_RECIEVED,
            OpportunityStatus.INSOMEA_QUOTE_CREATED,
            OpportunityStatus.CLIENT_PO_REQUEST,
            OpportunityStatus.CLIENT_PO_RECIEVED,
        ]
    )
    
    return subscriptions.order_by('current_term_end')
