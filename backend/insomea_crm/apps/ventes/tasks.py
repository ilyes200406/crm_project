"""
CELERY TASKS - APP OPPORTUNITIES

Tasks asynchrones:
- Vérifier subscriptions expirant
- Envoyer notifications expiration
- Expire subscriptions non renouvelées
"""

import logging
from celery import shared_task
from django.utils.timezone import now
from django.db import transaction
from datetime import date, timedelta

from .models import Subscription, SubscriptionStatus
from .services.subscription_service import check_subscription_expiring

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# EXPIRATION CHECKS
# ═══════════════════════════════════════════════════════════

@shared_task(name='opportunities.tasks.check_expiring_subscriptions')
def check_expiring_subscriptions():
    """
    Vérifie subscriptions expirant bientôt

    Exécution: Daily 8am UTC (Celery Beat)

    Actions:
    1. Requête unique: subscriptions ACTIVE + auto_renew dans [3, 90] jours
    2. Pour chaque threshold [90, 60, 30, 7, 3]:
       - Vérifie idempotence (notified_days)
       - Envoi email client
       - Envoi notification commercial
    3. Si days_until_expiration <= 30:
       - Transition FSM: ACTIVE → PENDING_RENEWAL (résiliente aux pannes)

    Returns:
        dict stats
    """

    logger.info('Starting check_expiring_subscriptions task')

    today = now().date()
    thresholds = [90, 60, 30, 7, 3]
    max_days = max(thresholds)  # 90
    min_days = min(thresholds)  # 3

    stats = {
        'total_checked': 0,
        'notifications_sent': 0,
        'marked_pending_renewal': 0,
        'errors': 0,
    }

    # Single query: all ACTIVE auto-renew subscriptions expiring within range
    subscriptions = Subscription.objects.filter(
        status=SubscriptionStatus.ACTIVE,
        auto_renew=True,
        current_term_end__range=[
            today + timedelta(days=min_days),
            today + timedelta(days=max_days),
        ],
    ).select_related('client', 'product')

    logger.info(f'Found {subscriptions.count()} subscriptions in [{min_days}d, {max_days}d] range')

    for subscription in subscriptions:

        stats['total_checked'] += 1

        try:
            days_until_expiration = (subscription.current_term_end - today).days

            # Only act on exact threshold days
            if days_until_expiration not in thresholds:
                continue

            notified_days = subscription.notified_days or []

            # Idempotency: skip if already notified at this threshold
            if days_until_expiration in notified_days:
                logger.info(
                    f'Subscription {subscription.subscription_number}: '
                    f'already notified at {days_until_expiration}d, skipping'
                )
                continue

            # ───────────────────────────────────────────
            # 1. Envoi email client + notification commercial
            # ───────────────────────────────────────────

            send_renewal_reminder_email_client(
                subscription=subscription,
                days_until_expiration=days_until_expiration
            )
            notify_commercial_subscription_expiring(
                subscription=subscription,
                days_until_expiration=days_until_expiration
            )
            stats['notifications_sent'] += 1

            notified_days.append(days_until_expiration)
            subscription.notified_days = notified_days

            # ───────────────────────────────────────────
            # 2. FSM transition + save (atomic)
            # ───────────────────────────────────────────

            with transaction.atomic():
                if (
                    days_until_expiration <= 30 and
                    subscription.status == SubscriptionStatus.ACTIVE
                ):
                    subscription.mark_pending_renewal()
                    stats['marked_pending_renewal'] += 1
                    logger.info(
                        f'Subscription {subscription.subscription_number} → PENDING_RENEWAL '
                        f'({days_until_expiration}d remaining)'
                    )
                    subscription.save(update_fields=['status', 'notified_days'])
                else:
                    subscription.save(update_fields=['notified_days'])

        except Exception as e:
            logger.error(
                f'Error processing subscription {subscription.subscription_number}: {str(e)}'
            )
            stats['errors'] += 1
            continue

    logger.info(f'Task completed: {stats}')
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


# ═══════════════════════════════════════════════════════════
# TRANSACTIONAL EMAIL TASKS
# ═══════════════════════════════════════════════════════════

def _notify_email_failure(opportunity, message):
    """
    Creates an in-app notification when an email task exhausts all retries.
    Notifies: commercial assigned to the opportunity + all ADMIN users.
    """
    from .notifications.models import Notification, NotificationType
    from .notifications.services import send_notification_to_websocket
    from ..users.models.users import User

    recipients = set()
    if opportunity.assigned_to:
        recipients.add(opportunity.assigned_to)
    recipients.update(User.objects.filter(role_id='ADMIN', is_active=True))

    for user in recipients:
        notification = Notification.objects.create(
            type=NotificationType.EMAIL_FAILED,
            recipient=user,
            title=f"Échec envoi email – {opportunity.reference}",
            message=message,
            opportunity=opportunity,
            action_url=f"/opportunities/{opportunity.id}/",
        )
        try:
            send_notification_to_websocket(notification)
            notification.mark_as_sent()
        except Exception:
            notification.mark_as_failed()


@shared_task(
    name='opportunities.tasks.send_supplier_quote_request_email',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_supplier_quote_request_email(self, opportunity_id, supplier_id, line_ids):
    from .models import Opportunity, OpportunityLine
    from ..suppliers.models import Supplier
    from .emails.services import send_supplier_quote_request

    opportunity = Opportunity.objects.get(id=opportunity_id)
    supplier = Supplier.objects.get(id=supplier_id)
    lines = OpportunityLine.objects.filter(id__in=line_ids)

    try:
        send_supplier_quote_request(opportunity=opportunity, supplier=supplier, lines=lines)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            _notify_email_failure(
                opportunity,
                f"Impossible d'envoyer l'email de demande de devis au fournisseur {supplier.name} après 3 tentatives."
            )
        raise self.retry(exc=exc)


@shared_task(
    name='opportunities.tasks.send_client_quote_pdf_email',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_client_quote_pdf_email(self, opportunity_id, insomea_quote_id):
    from .models import Opportunity, InsomeaQuote
    from .emails.services import send_client_quote_with_pdf

    opportunity = Opportunity.objects.get(id=opportunity_id)
    insomea_quote = InsomeaQuote.objects.get(id=insomea_quote_id)

    try:
        send_client_quote_with_pdf(opportunity=opportunity, insomea_quote=insomea_quote)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            _notify_email_failure(
                opportunity,
                f"Impossible d'envoyer le devis PDF au client {opportunity.client.company_name} après 3 tentatives."
            )
        raise self.retry(exc=exc)


@shared_task(
    name='opportunities.tasks.send_insomea_po_email',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_insomea_po_email(self, supplier_id, po_id, opportunity_id):
    from .models import Opportunity, InsomeaPurchaseOrder
    from ..suppliers.models import Supplier
    from .emails.services import send_insomea_po_to_supplier

    supplier = Supplier.objects.get(id=supplier_id)
    po = InsomeaPurchaseOrder.objects.get(id=po_id)
    opportunity = Opportunity.objects.get(id=opportunity_id)

    try:
        send_insomea_po_to_supplier(supplier=supplier, po=po, opportunity=opportunity)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            _notify_email_failure(
                opportunity,
                f"Impossible d'envoyer le BC Insomea {po.po_number} au fournisseur {supplier.name} après 3 tentatives."
            )
        raise self.retry(exc=exc)