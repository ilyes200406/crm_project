"""
NOTIFICATION SERVICES

Création et envoi notifications internes
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

from .models import Notification, NotificationType, NotificationStatus


# ═══════════════════════════════════════════════════════════
# OPPORTUNITY WORKFLOW NOTIFICATIONS
# ═══════════════════════════════════════════════════════════

def notify_finance_to_approve(opportunity):
    """
    Notification Finance: Client PO reçu, approuver opportunité
    
    Args:
        opportunity: Opportunity instance
    
    Triggered by:
        Signal post_transition Opportunity (CLIENT_PO_RECEIVED)
    """
    
    from ...users.models.users import User
    
    # Get all FINANCE users
    finance_users = User.objects.filter(role='FINANCE', is_active=True)
    
    for user in finance_users:
        
        # Créé notification
        notification = Notification.objects.create(
            type=NotificationType.FINANCE_APPROVE,
            recipient=user,
            title=f"Opportunité {opportunity.reference} à approuver",
            message=f"Le bon de commande client a été reçu pour {opportunity.name}. Action requise: approuver l'opportunité.",
            opportunity=opportunity,
            action_url=f"/opportunities/{opportunity.id}/",
        )
        
        # Envoi email
        try:
            send_notification_email(notification)
            notification.mark_as_sent()
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            notification.mark_as_failed()


# ═══════════════════════════════════════════════════════════
# PROVISION WORKFLOW NOTIFICATIONS
# ═══════════════════════════════════════════════════════════

def notify_techniciens_provision_waiting(provision):
    """
    Notification Techniciens: Provision en attente
    
    Args:
        provision: Provision instance
    
    Triggered by:
        Signal post_save Provision (status=WAITING_PROVISION)
    """
    
    from ...users.models.users import User
    
    # Get all TECHNICIEN users
    tech_users = User.objects.filter(role='TECHNICIEN', is_active=True)
    
    product_name = provision.opportunity_line.product.title
    opportunity_ref = provision.opportunity_line.opportunity.reference
    
    for user in tech_users:
        
        notification = Notification.objects.create(
            type=NotificationType.TECH_PROVISION_WAITING,
            recipient=user,
            title=f"Provision en attente: {product_name}",
            message=f"Une nouvelle provision est en attente pour {product_name} (Opportunité {opportunity_ref}).",
            provision=provision,
            opportunity=provision.opportunity_line.opportunity,
            action_url=f"/provisions/{provision.id}/",
        )
        
        try:
            send_notification_email(notification)
            notification.mark_as_sent()
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            notification.mark_as_failed()


def notify_all_provisioned(provision):
    """
    Notification tous: Subscription provisionnée
    
    Args:
        provision: Provision instance
    
    Triggered by:
        Signal post_transition Provision (PROVISIONED)
    """
    
    from ...users.models.users import User
    
    # Get commercial assigné + Finance + Tech teams
    opportunity = provision.opportunity_line.opportunity
    
    recipients = set()
    
    # Commercial assigné
    if opportunity.assigned_to:
        recipients.add(opportunity.assigned_to)
    
    # Finance team
    finance_users = User.objects.filter(role='FINANCE', is_active=True)
    recipients.update(finance_users)
    
    # Technicien qui a provisionné
    if provision.provisionned_by:
        recipients.add(provision.provisionned_by)
    
    product_name = provision.opportunity_line.product.title
    subscription_number = provision.microsoft_subscription_id
    
    for user in recipients:
        
        notification = Notification.objects.create(
            type=NotificationType.SUBSCRIPTION_PROVISIONED,
            recipient=user,
            title=f"Subscription provisionnée: {product_name}",
            message=f"La subscription {subscription_number} pour {product_name} a été provisionnée avec succès.",
            provision=provision,
            subscription=provision.subscription,
            opportunity=opportunity,
            action_url=f"/subscriptions/{provision.subscription.id}/",
        )
        
        try:
            send_notification_email(notification)
            notification.mark_as_sent()
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            notification.mark_as_failed()


# ═══════════════════════════════════════════════════════════
# SUBSCRIPTION EXPIRATION NOTIFICATIONS
# ═══════════════════════════════════════════════════════════

def notify_subscription_expiring(subscription, days, recipient):
    """
    Notification: Subscription expire bientôt
    
    Args:
        subscription: Subscription instance
        days: int jours avant expiration
        recipient: User instance (commercial assigné)
    
    Triggered by:
        Celery task check_expiring_subscriptions
    """
    
    notification = Notification.objects.create(
        type=NotificationType.SUBSCRIPTION_EXPIRING,
        recipient=recipient,
        title=f"Subscription expire dans {days} jours",
        message=f"La subscription {subscription.subscription_number} pour {subscription.product.title} expire dans {days} jours. Créer opportunité renouvellement.",
        subscription=subscription,
        action_url=f"/subscriptions/{subscription.id}/",
    )
    
    try:
        send_notification_email(notification)
        notification.mark_as_sent()
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        notification.mark_as_failed()


def notify_subscription_expired(subscription):
    """
    Notification teams: Subscription expirée
    
    Args:
        subscription: Subscription instance
    
    Triggered by:
        Celery task expire_unrenewed_subscriptions
    """
    
    from ...users.models.users import User
    
    # Notifier Finance + Commercial assigné + Admin
    recipients = set()
    
    # Finance team
    finance_users = User.objects.filter(role='FINANCE', is_active=True)
    recipients.update(finance_users)
    
    # Commercial assigné (from Term 1)
    first_term = subscription.terms.filter(term_number=1).first()
    if first_term and first_term.opportunity.assigned_to:
        recipients.add(first_term.opportunity.assigned_to)
    
    # Admin
    admin_users = User.objects.filter(role='ADMIN', is_active=True)
    recipients.update(admin_users)
    
    for user in recipients:
        
        notification = Notification.objects.create(
            type=NotificationType.SUBSCRIPTION_EXPIRED,
            recipient=user,
            title=f"Subscription expirée: {subscription.product.title}",
            message=f"La subscription {subscription.subscription_number} pour le client {subscription.client.company_name} a expiré sans renouvellement.",
            subscription=subscription,
            action_url=f"/subscriptions/{subscription.id}/",
        )
        
        try:
            send_notification_email(notification)
            notification.mark_as_sent()
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            notification.mark_as_failed()


# ═══════════════════════════════════════════════════════════
# EMAIL SENDING
# ═══════════════════════════════════════════════════════════

def send_notification_email(notification):
    """
    Envoi email notification
    
    Args:
        notification: Notification instance
    """
    
    # Map type → template
    template_map = {
        NotificationType.FINANCE_APPROVE: 'notifications/finance_approve.html',
        NotificationType.TECH_PROVISION_WAITING: 'notifications/tech_provision_waiting.html',
        NotificationType.SUBSCRIPTION_PROVISIONED: 'notifications/subscription_provisioned.html',
        NotificationType.SUBSCRIPTION_EXPIRING: 'notifications/subscription_expiring.html',
        NotificationType.SUBSCRIPTION_EXPIRED: 'notifications/subscription_expired.html',
    }
    
    template_name = template_map.get(notification.type)
    
    if not template_name:
        print(f"⚠️  No template for notification type: {notification.type}")
        return
    
    # Render email
    context = {
        'notification': notification,
        'recipient': notification.recipient,
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
    }
    
    html_message = render_to_string(template_name, context)
    
    # Send
    send_mail(
        subject=notification.title,
        message=notification.message,  # Plain text fallback
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[notification.recipient.email],
        html_message=html_message,
        fail_silently=False,
    )