"""
SUBSCRIPTION SERVICE

Business logic gestion subscriptions:
- Création initiale
- Renouvellement
- Annulation
- Suspension
- Calculs
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from ..models import (
    Subscription,
    SubscriptionTerm,
    SubscriptionStatus,
)


# ═══════════════════════════════════════════════════════════
# CRÉATION SUBSCRIPTION
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def create_initial_subscription(
    *,
    subscription_number: str,
    provision,
    opportunity_line,
    start_date: date,
    end_date: date,
    unit_price_purchase: Decimal,
    unit_price_sale: Decimal
):
    """
    Crée subscription initiale (Term 1)
    
    Args:
        subscription_number: str Microsoft subscription ID
        provision: Provision instance
        opportunity_line: OpportunityLine instance
        start_date: date début
        end_date: date fin
        unit_price_purchase: Decimal prix achat
        unit_price_sale: Decimal prix vente
    
    Returns:
        dict {
            'subscription': Subscription,
            'term': SubscriptionTerm
        }
    
    Raises:
        ValidationError: Si données invalides
    
    Business Rules:
        - Subscription créée en PENDING_ACTIVATION
        - Term 1 créé
        - Link provision → subscription
        - FSM: activate() appelé
        - Status: PENDING_ACTIVATION → ACTIVE
    
    Called by:
        provision_service.complete_provisioning() (initial)
    """
    
    # ───────────────────────────────────────────────────────
    # 1. VALIDATION
    # ───────────────────────────────────────────────────────
    
    if end_date <= start_date:
        raise ValidationError('end_date doit être après start_date')
    
    if Subscription.objects.filter(subscription_number=subscription_number).exists():
        raise ValidationError(f'Subscription {subscription_number} existe déjà')
    
    if unit_price_sale < unit_price_purchase:
        raise ValidationError('Prix vente doit être >= prix achat')
    
    # ───────────────────────────────────────────────────────
    # 2. CRÉATION SUBSCRIPTION
    # ───────────────────────────────────────────────────────
    
    subscription = Subscription.objects.create(
        subscription_number=subscription_number,
        provision=provision,  # First provision
        product=opportunity_line.product,
        client=opportunity_line.opportunity.client,
        quantity=opportunity_line.quantity,
        billing_cycle=opportunity_line.billing_cycle,
        current_term_start=start_date,
        current_term_end=end_date,
        auto_renew=True,
        status=SubscriptionStatus.PENDING_ACTIVATION,
    )
    
    # ───────────────────────────────────────────────────────
    # 3. CRÉATION TERM 1
    # ───────────────────────────────────────────────────────
    
    term = SubscriptionTerm.objects.create(
        subscription=subscription,
        opportunity=opportunity_line.opportunity,
        provision=provision,
        term_number=1,
        start_date=start_date,
        end_date=end_date,
        unit_price_purchase=unit_price_purchase,
        unit_price_sale=unit_price_sale,
        # total_* calculés dans save()
        auto_renew_enabled=True,
    )
    
    # ───────────────────────────────────────────────────────
    # 4. LINK PROVISION → SUBSCRIPTION
    # ───────────────────────────────────────────────────────
    
    provision.subscription = subscription
    provision.subscription_term = term
    provision.save(update_fields=['subscription', 'subscription_term'])
    
    # ───────────────────────────────────────────────────────
    # 5. ACTIVATION (FSM)
    # ───────────────────────────────────────────────────────
    
    subscription.activate()
    subscription.save()
    # Signal FSM → StatusHistory créé auto
    
    return {
        'subscription': subscription,
        'term': term,
    }


# ═══════════════════════════════════════════════════════════
# RENOUVELLEMENT SUBSCRIPTION
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def renew_subscription(
    *,
    subscription,
    provision,
    opportunity,
    start_date: date,
    end_date: date,
    unit_price_purchase: Decimal,
    unit_price_sale: Decimal
):
    """
    Renouvelle subscription existante (Term N)
    
    Args:
        subscription: Subscription instance (existante)
        provision: Provision instance (renewal)
        opportunity: Opportunity instance (RENEWAL)
        start_date: date début nouveau terme
        end_date: date fin nouveau terme
        unit_price_purchase: Decimal prix achat
        unit_price_sale: Decimal prix vente
    
    Returns:
        dict {
            'subscription': Subscription (updated),
            'term': SubscriptionTerm (nouveau)
        }
    
    Raises:
        ValidationError: Si données invalides
    
    Business Rules:
        - Récupère term_number max + 1
        - Crée SubscriptionTerm N
        - Update subscription.current_term_*
        - FSM: renew(term)
        - Status: PENDING_RENEWAL → ACTIVE
        - Link provision → subscription_term
    
    Called by:
        provision_service.complete_provisioning() (renewal)
    """
    
    # ───────────────────────────────────────────────────────
    # 1. VALIDATION
    # ───────────────────────────────────────────────────────
    
    if end_date <= start_date:
        raise ValidationError('end_date doit être après start_date')
    
    if subscription.status not in [SubscriptionStatus.PENDING_RENEWAL, SubscriptionStatus.ACTIVE]:
        raise ValidationError(
            f'Subscription doit être ACTIVE ou PENDING_RENEWAL pour renouveler. '
            f'Status actuel : {subscription.get_status_display()}'
        )
    
    if unit_price_sale < unit_price_purchase:
        raise ValidationError('Prix vente doit être >= prix achat')
    
    # ───────────────────────────────────────────────────────
    # 2. CALCULE TERM NUMBER
    # ───────────────────────────────────────────────────────
    
    latest_term = subscription.get_latest_term()
    
    if latest_term:
        new_term_number = latest_term.term_number + 1
    else:
        # Cas edge: subscription sans terme (ne devrait pas arriver)
        new_term_number = 1
    
    # ───────────────────────────────────────────────────────
    # 3. CRÉATION NOUVEAU TERM
    # ───────────────────────────────────────────────────────
    
    term = SubscriptionTerm.objects.create(
        subscription=subscription,
        opportunity=opportunity,
        provision=provision,
        term_number=new_term_number,
        start_date=start_date,
        end_date=end_date,
        unit_price_purchase=unit_price_purchase,
        unit_price_sale=unit_price_sale,
        # total_* calculés dans save()
        auto_renew_enabled=subscription.auto_renew,
    )
    
    # ───────────────────────────────────────────────────────
    # 4. UPDATE SUBSCRIPTION
    # ───────────────────────────────────────────────────────
    
    # Update current_term_*
    subscription.current_term_start = start_date
    subscription.current_term_end = end_date
    
    # FSM: renew(term)
    if subscription.status == SubscriptionStatus.PENDING_RENEWAL:
        subscription.renew(new_term=term)
    
    subscription.save()
    # Signal FSM → StatusHistory créé auto
    
    # ───────────────────────────────────────────────────────
    # 5. LINK PROVISION → SUBSCRIPTION_TERM
    # ───────────────────────────────────────────────────────
    
    provision.subscription = subscription
    provision.subscription_term = term
    provision.save(update_fields=['subscription', 'subscription_term'])
    
    return {
        'subscription': subscription,
        'term': term,
    }


# ═══════════════════════════════════════════════════════════
# ANNULATION / SUSPENSION
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def cancel_subscription(*, subscription, reason='', user=None):
    """
    Annule subscription
    
    Args:
        subscription: Subscription instance
        reason: str raison annulation
        user: User instance (pour audit)
    
    Returns:
        Subscription (updated)
    
    Business Rules:
        - FSM: cancel()
        - Status: ANY → CANCELLED
    """
    
    subscription.cancel(reason=reason)
    subscription.save()
    # Signal FSM → StatusHistory créé auto
    
    return subscription


@transaction.atomic
def suspend_subscription(*, subscription, reason='', user=None):
    """
    Suspend subscription
    
    Args:
        subscription: Subscription instance
        reason: str raison suspension
        user: User instance
    
    Returns:
        Subscription (updated)
    
    Business Rules:
        - FSM: suspend()
        - Status: ACTIVE → SUSPENDED
    """
    
    if subscription.status != SubscriptionStatus.ACTIVE:
        raise ValidationError('Seules subscriptions ACTIVE peuvent être suspendues')
    
    subscription.suspend(reason=reason)
    subscription.save()
    # Signal FSM → StatusHistory créé auto
    
    return subscription


@transaction.atomic
def reactivate_subscription(*, subscription, user=None):
    """
    Réactive subscription suspendue
    
    Args:
        subscription: Subscription instance
        user: User instance
    
    Returns:
        Subscription (updated)
    
    Business Rules:
        - FSM: reactivate()
        - Status: SUSPENDED → ACTIVE
    """
    
    if subscription.status != SubscriptionStatus.SUSPENDED:
        raise ValidationError('Seules subscriptions SUSPENDED peuvent être réactivées')
    
    subscription.reactivate()
    subscription.save()
    # Signal FSM → StatusHistory créé auto
    
    return subscription


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def check_subscription_expiring(subscription, days=30):
    """
    Vérifie si subscription expire bientôt
    
    Args:
        subscription: Subscription instance
        days: int seuil jours
    
    Returns:
        bool
    """
    return subscription.is_expiring_soon(days=days)


def get_subscription_revenue_metrics(subscription):
    """
    Calcule métriques revenue subscription
    
    Args:
        subscription: Subscription instance
    
    Returns:
        dict {
            'total_revenue': Decimal (tous termes),
            'total_cost': Decimal (tous termes),
            'total_margin': Decimal,
            'avg_margin_percent': Decimal,
            'terms_count': int,
        }
    """
    
    terms = subscription.get_all_terms()
    
    total_revenue = sum(t.total_sale for t in terms)
    total_cost = sum(t.total_purchase for t in terms)
    total_margin = total_revenue - total_cost
    
    avg_margin_percent = Decimal('0.00')
    if total_cost > 0:
        avg_margin_percent = (total_margin / total_cost) * Decimal('100.00')
    
    return {
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_margin': total_margin,
        'avg_margin_percent': avg_margin_percent,
        'terms_count': terms.count(),
    }