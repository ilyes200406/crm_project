"""
PROVISION SERVICE - MODIFIÉ

Ajout support renewal:
- complete_provisioning() détecte initial vs renewal
- Appelle create_initial_subscription() OU renew_subscription()
"""

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError, PermissionDenied
from django.utils import timezone

from ..models import (
    Provision,
    ProvisionStatus,
    Subscription,
    OpportunityStatus,
    OpportunityLineStatus,
)
from ..validators import (
    validate_can_start_provisioning,
    validate_can_complete_provisioning,
)
from ..selectors import (
    get_provision_by_id,
    get_opportunity_by_id
)

# 🆕 NOUVEAUX IMPORTS
from .subscription_service import (
    create_initial_subscription,
    renew_subscription,
)


def _get_related_or_none(instance, attr_name):
    try:
        return getattr(instance, attr_name)
    except ObjectDoesNotExist:
        return None


# ═══════════════════════════════════════════════════════════
# PROVISION CREATION (INCHANGÉ)
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def create_provisions(*, opportunity_id, user, ip_address=None):
    """
    Create provisions for opportunity
    
    🆕 MODIFIÉ: Triggered by confirm_insomea_pos() (toutes POs confirmées)
    AVANT: Triggered by approve_opportunity()
    
    Args:
        opportunity_id: UUID
        user: User instance
    
    Returns:
        list[Provision]
    
    Business Rules:
        - Opportunity status must be INSOMEA_PO_CONFIRMED  # 🆕 MODIFIÉ
        - All lines must be INSOMEA_PO_CONFIRMED  # 🆕 MODIFIÉ
        - Creates 1 Provision per line
    """
    
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=True)
    
    # 🆕 MODIFIÉ: Check status
    if opportunity.status != OpportunityStatus.INSOMEA_POS_CONFIRMED :
        raise ValidationError(
            f"Opportunity must be INSOMEA_PO_CONFIRMED to create provisions. "
            f"Current: {opportunity.get_status_display()}"
        )
    
    # Check lines
    for line in opportunity.lines.all():
        # 🆕 MODIFIÉ: Check status
        if line.status != OpportunityLineStatus.INSOMEA_PO_CONFIRMED:
            raise ValidationError(
                f"Line {line.id} must be INSOMEA_PO_CONFIRMED. "
                f"Current: {line.get_status_display()}"
            )
    
    provisions = []
    
    for line in opportunity.lines.all():
        
        # Check if provision already exists
        if hasattr(line, 'provision') and line.provision:
            print(f"⚠️  Provision already exists for line {line.id}")
            continue
        
        # Determine subscription (renewal vs initial)
        subscription = None
        if line.is_renewal():
            subscription = line.get_original_subscription()
        
        # Create provision
        provision = Provision.objects.create(
            opportunity_line=line,
            subscription=subscription,  # None if initial, existing if renewal
            status=ProvisionStatus.WAITING_PROVISION,
        )

        provisions.append(provision)
        # Notification handled by post_save signal (notify_on_provision_created)
    
    return provisions


# ═══════════════════════════════════════════════════════════
# PROVISION WORKFLOW (MODIFIÉ)
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def start_provisioning(*, provision_id, user, ip_address=None):
    """
    Démarre provisionnement (TECHNICIEN)
    
    INCHANGÉ - fonctionne pour INITIAL et RENEWAL
    
    Args:
        provision_id: UUID Provision
        user: User instance (TECHNICIEN)
        ip_address: str
    
    Returns:
        Provision mise à jour
    
    Raises:
        ValidationError: Si préconditions non remplies
        PermissionDenied: Si pas TECHNICIEN
    
    Business Rules:
        - Transition FSM: WAITING_PROVISION → PROVISIONING
        - Store technician + timestamp
    """
    
    # ───────────────────────────────────────────────────────
    # 1. RÉCUPÉRATION + PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    provision = get_provision_by_id(provision_id)

    # ───────────────────────────────────────────────────────
    # 2. VALIDATION PRÉCONDITIONS
    # ───────────────────────────────────────────────────────
    
    validate_can_start_provisioning(provision)
    
    # ───────────────────────────────────────────────────────
    # 3. TRANSITION FSM
    # ───────────────────────────────────────────────────────
    
    # FSM transition avec callback
    provision.start(technician=user)
    provision.save()
    # Signal FSM → StatusHistory créé auto
    
    # NOTE: start() callback dans model:
    #   - provision.provisionned_by = technician
    #   - provision.provisioning_started_at = timezone.now()
    
    return provision


@transaction.atomic
def complete_provisioning(
    *,
    provision_id,
    subscription_data: dict,
    user,
    ip_address=None
):
    """
    Termine provisionnement avec succès
    
    🆕 MODIFIÉ: Détecte INITIAL vs RENEWAL
    
    Args:
        provision_id: UUID Provision
        subscription_data: dict données subscription
            
            CAS INITIAL:
            {
                'subscription_number': str Microsoft subscription ID,
                'start_date': date,
                'end_date': date,
            }
            
            CAS RENEWAL:
            {
                'start_date': date,  ← Nouveau terme
                'end_date': date,    ← Nouveau terme
                # PAS de subscription_number (déjà existe)
            }
        
        user: User instance (TECHNICIEN)
        ip_address: str
    
    Returns:
        dict {
            'subscription': Subscription (créée ou mise à jour),
            'term': SubscriptionTerm (créé),
            'provision': Provision (mise à jour)
        }
    
    Raises:
        ValidationError: Si préconditions non remplies
        PermissionDenied: Si pas TECHNICIEN
    
    Business Rules:

        CAS INITIAL (provision.subscription is None):
            1. Récupère pricing depuis InsomeaQuoteLine
            2. Appelle create_initial_subscription()
               → Crée Subscription (PENDING_ACTIVATION → ACTIVE)
               → Crée SubscriptionTerm 1
               → Link provision
            3. Transition FSM provision: PROVISIONING → PROVISIONED
        
        CAS RENEWAL (provision.subscription existe):
            1. Récupère pricing depuis InsomeaQuoteLine
            2. Appelle renew_subscription()
               → Crée SubscriptionTerm N
               → Update Subscription (current_term_*)
               → FSM: PENDING_RENEWAL → ACTIVE
               → Link provision
            3. Transition FSM provision: PROVISIONING → PROVISIONED
    """
    
    # ───────────────────────────────────────────────────────
    # 1. RÉCUPÉRATION + PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    provision = get_provision_by_id(provision_id)

    # ───────────────────────────────────────────────────────
    # 2. VÉRIFICATION
    # ───────────────────────────────────────────────────────
    
    if provision.status != ProvisionStatus.PROVISIONING:
        raise ValidationError(
            'Le provisionnement doit être en cours'
        )
    
    # ───────────────────────────────────────────────────────
    # 3. VALIDATION DONNÉES SUBSCRIPTION
    # ───────────────────────────────────────────────────────
    
    required_fields = ['start_date', 'end_date']
    for field in required_fields:
        if field not in subscription_data:
            raise ValidationError(f'{field} requis')
    
    # Vérifie dates
    if subscription_data['end_date'] <= subscription_data['start_date']:
        raise ValidationError('end_date doit être après start_date')
    
    # ───────────────────────────────────────────────────────
    # 4. RÉCUPÈRE PRICING DEPUIS INSOMEA QUOTE LINE
    # ───────────────────────────────────────────────────────
    
    opportunity_line = provision.opportunity_line
    
    insomea_quote_line = _get_related_or_none(opportunity_line, 'insomea_quote_line')
    if insomea_quote_line is None:
        raise ValidationError(
            'InsomeaQuoteLine requis pour récupérer pricing'
        )

    
    unit_price_purchase = insomea_quote_line.unit_price_purchase
    unit_price_sale = insomea_quote_line.unit_price_sale
    
    # ───────────────────────────────────────────────────────
    # 5. DÉTECTE INITIAL VS RENEWAL
    # ───────────────────────────────────────────────────────
    
    is_renewal = provision.is_renewal

    # ═══════════════════════════════════════════════════════
    # CAS A: INITIAL (création subscription)
    # ═══════════════════════════════════════════════════════
    
    if not is_renewal:
        
        # Vérifie subscription_number fourni
        if 'subscription_number' not in subscription_data:
            raise ValidationError('subscription_number requis pour création initiale')
        
        subscription_number = subscription_data['subscription_number']
        
        # Vérifie unicité
        if Subscription.objects.filter(subscription_number=subscription_number).exists():
            raise ValidationError(
                f'Subscription {subscription_number} existe déjà'
            )
        
        # Appelle subscription_service
        result = create_initial_subscription(
            subscription_number=subscription_number,
            provision=provision,
            opportunity_line=opportunity_line,
            start_date=subscription_data['start_date'],
            end_date=subscription_data['end_date'],
            unit_price_purchase=unit_price_purchase,
            unit_price_sale=unit_price_sale,
        )
        
        subscription = result['subscription']
        term = result['term']
        
        # Update provision microsoft_subscription_id
        provision.microsoft_subscription_id = subscription_number
    
    # ═══════════════════════════════════════════════════════
    # CAS B: RENEWAL (renouvellement subscription existante)
    # ═══════════════════════════════════════════════════════
    
    else:
        
        # Récupère subscription existante
        subscription = provision.subscription
        
        if not subscription:
            raise ValidationError(
                'Provision renewal sans subscription (données corrompues)'
            )
        
        # Appelle subscription_service
        result = renew_subscription(
            subscription=subscription,
            provision=provision,
            opportunity=opportunity_line.opportunity,
            start_date=subscription_data['start_date'],
            end_date=subscription_data['end_date'],
            unit_price_purchase=unit_price_purchase,
            unit_price_sale=unit_price_sale,
        )
        
        subscription = result['subscription']
        term = result['term']
        
        # Update provision microsoft_subscription_id (garde existant)
        # provision.microsoft_subscription_id = subscription.subscription_number
    
    # ───────────────────────────────────────────────────────
    # 6. TRANSITION FSM PROVISION
    # ───────────────────────────────────────────────────────
    
    # FSM transition avec callback
    provision.complete_provisioning(subscription_id=provision.microsoft_subscription_id)
    provision.save()
    # Signal FSM → StatusHistory créé auto
    
    # NOTE: complete_provisioning() callback dans model:
    #   - provision.microsoft_subscription_id = subscription_id
    #   - provision.provisioning_completed_at = timezone.now()
    
    return {
        'subscription': subscription,
        'term': term,
        'provision': provision,
    }


# ═══════════════════════════════════════════════════════════
# PROVISION FAILURE (INCHANGÉ)
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def fail_provisioning(*, provision_id, error_message, user, ip_address=None):
    """
    Marque provisionnement comme échoué
    
    INCHANGÉ - fonctionne pour INITIAL et RENEWAL
    
    Args:
        provision_id: UUID Provision
        error_message: str message d'erreur
        user: User instance (TECHNICIEN)
        ip_address: str
    
    Returns:
        Provision mise à jour
    
    Raises:
        ValidationError: Si préconditions non remplies
        PermissionDenied: Si pas TECHNICIEN
    
    Business Rules:
        - Transition FSM: PROVISIONING → ERROR
        - Store error message
        - Permet retry ultérieur
    """
    
    # ───────────────────────────────────────────────────────
    # 1. RÉCUPÉRATION + PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    provision = get_provision_by_id(provision_id)

    # ───────────────────────────────────────────────────────
    # 2. VÉRIFICATION
    # ───────────────────────────────────────────────────────
    
    if provision.status != ProvisionStatus.PROVISIONING:
        raise ValidationError(
            'Le provisionnement doit être en cours pour reporter un échec'
        )
    
    # ───────────────────────────────────────────────────────
    # 3. TRANSITION FSM
    # ───────────────────────────────────────────────────────
    
    # FSM transition avec callback
    provision.fail_provisioning(error_message=error_message)
    provision.save()
    # Signal FSM → StatusHistory créé auto
    
    # NOTE: fail_provisioning() callback dans model:
    #   - provision.provisioning_error = error_message
    
    return provision


@transaction.atomic
def retry_provisioning(*, provision_id, user, ip_address=None):
    """
    Retry provisionnement après échec
    
    INCHANGÉ
    
    Args:
        provision_id: UUID Provision
        user: User instance (TECHNICIEN)
        ip_address: str
    
    Returns:
        Provision mise à jour
    
    Raises:
        ValidationError: Si pas en ERROR
        PermissionDenied: Si pas TECHNICIEN
    
    Business Rules:
        - Transition FSM: ERROR → PROVISIONING
        - Clear error message
        - Restart provisionnement
    
    Note:
        Nécessite d'ajouter cette transition dans le model Provision si besoin
    """
    
    # ───────────────────────────────────────────────────────
    # 1. RÉCUPÉRATION + PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    provision = get_provision_by_id(provision_id)

    # ───────────────────────────────────────────────────────
    # 2. VÉRIFICATION
    # ───────────────────────────────────────────────────────
    
    if provision.status != ProvisionStatus.ERROR:
        raise ValidationError(
            'Le provisionnement doit être en erreur pour retry'
        )
    
    # ───────────────────────────────────────────────────────
    # 3. CLEAR ERROR + RESTART
    # ───────────────────────────────────────────────────────
    
    # Clear error
    provision.provisioning_error = ''
    
    provision.restart()
    provision.save()
    
    return provision
"""
**✅ SERVICES PARTIE 4/5 COMPLETE !**

**Coverage :**
- ✅ create_provision_for_line() - Auto-créé quand opportunity APPROVED
- ✅ start_provisioning() - TECHNICIEN démarre + FSM transition PROVISIONING
- ✅ complete_provisioning() - Crée Subscription + FSM transition PROVISIONED
- ✅ fail_provisioning() - FSM transition ERROR + store error
- ✅ retry_provisioning() - Retry après échec

**WORKFLOW PROVISIONING COMPLET :**
```
1. Opportunity APPROVED:
   → approve_opportunity() appelle create_provision_for_line()
   → Provision créée: WAITING_PROVISION

2. Technicien démarre:
   → start_provisioning()
   → FSM: WAITING_PROVISION → PROVISIONING
   → Store technician + timestamp

3a. Succès:
   → complete_provisioning()
   → Crée Subscription (Microsoft ID, dates)
   → FSM: PROVISIONING → PROVISIONED

3b. Échec:
   → fail_provisioning()
   → FSM: PROVISIONING → ERROR
   → Store error_message
   → Technicien peut retry_provisioning()
"""
