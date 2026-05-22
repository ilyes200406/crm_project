"""
CELERY TASKS - APP OPPORTUNITIES

Tasks asynchrones:
- Gérer expirations subscriptions (pending renewal + expiration)
- Envoyer emails transactionnels (devis, BCs)
"""

import logging
from celery import shared_task
from django.db import transaction
from datetime import date, timedelta

from .models import Subscription, SubscriptionStatus

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# EXPIRATION CHECKS
# ═══════════════════════════════════════════════════════════

@shared_task(name='opportunities.tasks.process_subscription_expirations')
def process_subscription_expirations():
    """
    Daily task — two passes:

    Pass 1 (ACTIVE → PENDING_RENEWAL):
        Any ACTIVE subscription with current_term_end <= today + 30 days.
        Transitions FSM, sends email + notifies commercial once.
        Idempotency: guaranteed by FSM state — once PENDING_RENEWAL, not picked up again.

    Pass 2 (PENDING_RENEWAL → EXPIRED):
        Any PENDING_RENEWAL subscription with current_term_end < today.
        Skipped if a renewal opportunity is in progress.
        Sends expiration email + notifies commercial once.

    Returns:
        dict stats
    """

    today = date.today()
    stats = {
        'marked_pending': 0,
        'expired': 0,
        'renewal_skipped': 0,
        'errors': 0,
    }

    # ───────────────────────────────────────────────────────
    # PASS 1: ACTIVE → PENDING_RENEWAL
    # ───────────────────────────────────────────────────────

    expiring_soon = Subscription.objects.filter(
        status=SubscriptionStatus.ACTIVE,
        current_term_end__lte=today + timedelta(days=30),
    ).select_related('client', 'product')

    for subscription in expiring_soon:
        try:
            days_left = (subscription.current_term_end - today).days

            with transaction.atomic():
                subscription.mark_pending_renewal()
                subscription.save(update_fields=['status'])

            send_renewal_reminder_email_client(
                subscription=subscription,
                days_until_expiration=days_left,
            )
            notify_commercial_subscription_expiring(
                subscription=subscription,
                days_until_expiration=days_left,
            )

            stats['marked_pending'] += 1
            logger.info(
                f'Subscription {subscription.subscription_number} → PENDING_RENEWAL '
                f'({days_left}d remaining)'
            )

        except Exception as e:
            logger.error(
                f'Error marking pending renewal for {subscription.subscription_number}: {e}'
            )
            stats['errors'] += 1

    # ───────────────────────────────────────────────────────
    # PASS 2: PENDING_RENEWAL → EXPIRED
    # ───────────────────────────────────────────────────────

    from .models import OpportunityStatus

    overdue = Subscription.objects.filter(
        status=SubscriptionStatus.PENDING_RENEWAL,
        current_term_end__lt=today,
    ).select_related('client', 'product').prefetch_related('renewal_lines')

    for subscription in overdue:
        try:
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
                stats['renewal_skipped'] += 1
                logger.info(
                    f'Subscription {subscription.subscription_number} has renewal in progress, skipping'
                )
                continue

            with transaction.atomic():
                subscription.expire()
                subscription.save()

            send_subscription_expired_email_client(subscription)
            notify_teams_subscription_expired(subscription)

            stats['expired'] += 1
            logger.info(f'Subscription {subscription.subscription_number} → EXPIRED')

        except Exception as e:
            logger.error(
                f'Error expiring subscription {subscription.subscription_number}: {e}'
            )
            stats['errors'] += 1

    logger.info(f'process_subscription_expirations completed: {stats}')
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