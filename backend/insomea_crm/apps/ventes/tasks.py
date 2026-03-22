"""
CELERY TASKS - APP OPPORTUNITIES

Tasks asynchrones:
- Vérifier subscriptions expirant
- Envoyer notifications expiration
- Expire subscriptions non renouvelées
"""

from celery import shared_task
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import Subscription, SubscriptionStatus
from .services.subscription_service import check_subscription_expiring


# ═══════════════════════════════════════════════════════════
# EXPIRATION CHECKS
# ═══════════════════════════════════════════════════════════

@shared_task(name='opportunities.tasks.check_expiring_subscriptions')
def check_expiring_subscriptions():
    """
    Vérifie subscriptions expirant bientôt
    
    Exécution: Daily 8am UTC (Celery Beat)
    
    Actions:
    1. Pour chaque threshold [90, 60, 30, 7, 3] jours:
       - Find subscriptions expirant dans X jours
       - Envoi email client
       - Envoi notification commercial
    
    2. Si 30j avant expiration:
       - Transition FSM: ACTIVE → PENDING_RENEWAL
    
    Returns:
        dict stats
    """
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info('🔔 Starting check_expiring_subscriptions task')
    
    today = date.today()
    
    # Thresholds à vérifier
    thresholds = [90, 60, 30, 7, 3]
    
    stats = {
        'total_checked': 0,
        'notifications_sent': 0,
        'marked_pending_renewal': 0,
        'errors': 0,
    }
    
    for days in thresholds:
        
        # Date exacte expiration = today + days
        expiration_date = today + timedelta(days=days)
        
        # Find subscriptions expirant ce jour précis
        subscriptions = Subscription.objects.filter(
            status=SubscriptionStatus.ACTIVE,
            current_term_end=expiration_date,
            auto_renew=True,  # Seulement celles avec auto-renew
        ).select_related('client', 'product')
        
        logger.info(f'📅 Found {subscriptions.count()} subscriptions expiring in {days} days')
        
        for subscription in subscriptions:
            
            stats['total_checked'] += 1
            
            try:
                
                # ───────────────────────────────────────────
                # 1. Envoi email client
                # ───────────────────────────────────────────
                
                send_renewal_reminder_email_client(
                    subscription=subscription,
                    days_until_expiration=days
                )
                
                stats['notifications_sent'] += 1
                
                # ───────────────────────────────────────────
                # 2. Notification commercial assigné
                # ───────────────────────────────────────────
                
                notify_commercial_subscription_expiring(
                    subscription=subscription,
                    days_until_expiration=days
                )
                
                # ───────────────────────────────────────────
                # 3. Si 30j: mark PENDING_RENEWAL
                # ───────────────────────────────────────────
                
                if days == 30 and subscription.status == SubscriptionStatus.ACTIVE:
                    
                    subscription.mark_pending_renewal()
                    subscription.save()
                    # Signal FSM → StatusHistory créé auto
                    
                    stats['marked_pending_renewal'] += 1
                    
                    logger.info(
                        f'✅ Subscription {subscription.subscription_number} '
                        f'marked PENDING_RENEWAL (30 days)'
                    )
                
            except Exception as e:
                logger.error(
                    f'❌ Error processing subscription {subscription.subscription_number}: {str(e)}'
                )
                stats['errors'] += 1
                continue
    
    logger.info(f'✅ Task completed: {stats}')
    
    return stats


@shared_task(name='opportunities.tasks.expire_unrenewed_subscriptions')
def expire_unrenewed_subscriptions():
    """
    Expire subscriptions non renouvelées
    
    Exécution: Daily 9am UTC (Celery Beat)
    
    Actions:
    1. Find subscriptions PENDING_RENEWAL avec end_date < today
    2. Vérifie si renewal en cours (OpportunityLine.renewal_of_subscription)
    3. Si PAS de renewal:
       - Transition FSM: PENDING_RENEWAL → EXPIRED
       - Envoi email client (subscription expirée)
       - Notification teams
    
    Returns:
        dict stats
    """
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info('🔔 Starting expire_unrenewed_subscriptions task')
    
    today = date.today()
    
    # Find subscriptions PENDING_RENEWAL passées
    subscriptions = Subscription.objects.filter(
        status=SubscriptionStatus.PENDING_RENEWAL,
        current_term_end__lt=today,
    ).select_related('client', 'product').prefetch_related('renewal_lines')
    
    logger.info(f'📅 Found {subscriptions.count()} subscriptions to check for expiration')
    
    stats = {
        'total_checked': subscriptions.count(),
        'expired': 0,
        'renewal_in_progress': 0,
        'errors': 0,
    }
    
    for subscription in subscriptions:
        
        try:
            
            # ───────────────────────────────────────────────
            # 1. Vérifie si renewal en cours
            # ───────────────────────────────────────────────
            
            from .models import OpportunityStatus
            
            renewal_in_progress = subscription.renewal_lines.filter(
                opportunity__status__in=[
                    OpportunityStatus.DRAFT,
                    OpportunityStatus.SUPPLIER_QUOTE_REQUEST,
                    OpportunityStatus.SUPPLIER_QUOTE_RECIEVED,
                    OpportunityStatus.INSOMEA_QUOTE_CREATED,
                    OpportunityStatus.CLIENT_PO_REQUEST,
                    OpportunityStatus.CLIENT_PO_RECIEVED,
                ]
            ).exists()
            
            if renewal_in_progress:
                # Renewal en cours, pas toucher
                stats['renewal_in_progress'] += 1
                logger.info(
                    f'⏳ Subscription {subscription.subscription_number} '
                    f'has renewal in progress, skipping expiration'
                )
                continue
            
            # ───────────────────────────────────────────────
            # 2. Expire subscription
            # ───────────────────────────────────────────────
            
            subscription.expire()
            subscription.save()
            # Signal FSM → StatusHistory créé auto
            
            stats['expired'] += 1
            
            logger.info(
                f'❌ Subscription {subscription.subscription_number} EXPIRED '
                f'(end_date: {subscription.current_term_end})'
            )
            
            # ───────────────────────────────────────────────
            # 3. Notifications
            # ───────────────────────────────────────────────
            
            send_subscription_expired_email_client(subscription)
            notify_teams_subscription_expired(subscription)
            
        except Exception as e:
            logger.error(
                f'❌ Error expiring subscription {subscription.subscription_number}: {str(e)}'
            )
            stats['errors'] += 1
            continue
    
    logger.info(f'✅ Task completed: {stats}')
    
    return stats


# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS (EMAIL/NOTIFICATIONS)
# ═══════════════════════════════════════════════════════════

def send_renewal_reminder_email_client(subscription, days_until_expiration):
    """
    Envoi email renewal reminder au client
    
    Args:
        subscription: Subscription instance
        days_until_expiration: int
    
    Note:
        Implémentation dans opportunities/emails/services.py
        (à créer dans prochaine partie)
    """
    
    from .emails.services import send_renewal_reminder_client
    
    send_renewal_reminder_client(
        subscription=subscription,
        days=days_until_expiration
    )


def notify_commercial_subscription_expiring(subscription, days_until_expiration):
    """
    Notification commercial: subscription expire bientôt
    
    Args:
        subscription: Subscription instance
        days_until_expiration: int
    
    Note:
        Implémentation dans opportunities/notifications/services.py
        (à créer dans prochaine partie)
    """
    
    from .notifications.services import notify_subscription_expiring
    
    # Get commercial assigné
    first_term = subscription.terms.filter(term_number=1).first()
    if first_term and first_term.opportunity.assigned_to:
        commercial = first_term.opportunity.assigned_to
        
        notify_subscription_expiring(
            subscription=subscription,
            days=days_until_expiration,
            recipient=commercial
        )


def send_subscription_expired_email_client(subscription):
    """
    Envoi email client: subscription expirée
    
    Args:
        subscription: Subscription instance
    """
    
    from .emails.services import send_subscription_expired_client
    
    send_subscription_expired_client(subscription=subscription)


def notify_teams_subscription_expired(subscription):
    """
    Notification teams: subscription expirée
    
    Args:
        subscription: Subscription instance
    """
    
    from .notifications.services import notify_subscription_expired
    
    notify_subscription_expired(subscription=subscription)