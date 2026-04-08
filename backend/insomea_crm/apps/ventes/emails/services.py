"""
EMAIL SERVICES

Envoi emails externes:
- Clients
- Fournisseurs
"""

from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# SUPPLIER EMAILS
# ═══════════════════════════════════════════════════════════

def send_supplier_quote_request(opportunity, supplier, lines):
    """
    Email fournisseur: demande devis
    
    Args:
        opportunity: Opportunity instance
        supplier: Supplier instance
        lines: QuerySet[OpportunityLine] pour ce fournisseur
    
    Triggered by:
        workflow_service.request_all_supplier_quotes()
    """


    if not supplier.support_email:
        logger.warning(f"⚠️  Supplier {supplier.name} has no email")
        return
    
    context = {
        'supplier': supplier,
        'opportunity': opportunity,
        'lines': lines,
        'client': opportunity.client,
        'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }
    
    html_message = render_to_string('emails/supplier_quote_request.html', context)
    
    send_mail(
        subject=f"Demande de devis - {opportunity.reference}",
        message=f"Bonjour, nous souhaitons obtenir un devis pour les produits suivants...",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[supplier.support_email],
        html_message=html_message,
        fail_silently=False,
    )
    
    logger.info(f"✅ Email sent to supplier {supplier.name}")


# ═══════════════════════════════════════════════════════════
# CLIENT EMAILS
# ═══════════════════════════════════════════════════════════

def send_client_quote_with_pdf(opportunity, insomea_quote):
    """
    Email client: devis Insomea avec PDF attaché
    
    Args:
        opportunity: Opportunity instance
        insomea_quote: InsomeaQuote instance
    
    Triggered by:
        purchase_order_service.request_client_po_transition()
    """

    client = opportunity.client
    
    if not client.email:
        logger.warning(f"⚠️  Client {client.company_name} has no email")
        return
    
    context = {
        'client': client,
        'opportunity': opportunity,
        'insomea_quote': insomea_quote,
        'lines': insomea_quote.lines.all(),
        'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }
    
    html_message = render_to_string('emails/client_quote_request.html', context)
    
    # Create email with attachment
    email = EmailMultiAlternatives(
        subject=f"Devis Insomea - {insomea_quote.reference}",
        body=f"Bonjour, veuillez trouver ci-joint notre devis {insomea_quote.reference}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[client.email],
    )
    
    email.attach_alternative(html_message, "text/html")
    
    # Attach PDF if exists
    if insomea_quote.document:
        email.attach_file(insomea_quote.document.path)
    
    email.send(fail_silently=False)
    
    logger.info(f"✅ Email sent to client {client.company_name}")


def send_renewal_reminder_client(subscription, days):
    """
    Email client: reminder renouvellement
    
    Args:
        subscription: Subscription instance
        days: int jours avant expiration
    
    Triggered by:
        Celery task check_expiring_subscriptions
    """
    
    client = subscription.client
    
    if not client.email:
        logger.warning(f"⚠️  Client {client.company_name} has no email")
        return
    
    # Map days → template
    template_map = {
        90: 'emails/renewal_reminder_90d.html',
        60: 'emails/renewal_reminder_60d.html',
        30: 'emails/renewal_reminder_30d.html',
        7: 'emails/renewal_reminder_7d.html',
        3: 'emails/renewal_reminder_3d.html',
    }
    
    template_name = template_map.get(days, 'emails/renewal_reminder_30d.html')
    
    context = {
        'client': client,
        'subscription': subscription,
        'days': days,
        'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }
    
    html_message = render_to_string(template_name, context)
    
    send_mail(
        subject=f"Renouvellement subscription - {days} jours",
        message=f"Bonjour, votre subscription {subscription.product.title} expire dans {days} jours.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[client.email],
        html_message=html_message,
        fail_silently=False,
    )
    
    logger.info(f"✅ Renewal reminder ({days}d) sent to client {client.company_name}")


def send_subscription_expired_client(subscription):
    """
    Email client: subscription expirée
    
    Args:
        subscription: Subscription instance
    
    Triggered by:
        Celery task expire_unrenewed_subscriptions
    """
    
    client = subscription.client
    
    if not client.email:
        logger.warning(f"⚠️  Client {client.company_name} has no email")
        return
    
    context = {
        'client': client,
        'subscription': subscription,
        'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }
    
    html_message = render_to_string('emails/subscription_expired.html', context)
    
    send_mail(
        subject=f"Subscription expirée - {subscription.product.title}",
        message=f"Bonjour, votre subscription {subscription.product.title} a expiré.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[client.email],
        html_message=html_message,
        fail_silently=False,
    )
    
    logger.info(f"✅ Expiration email sent to client {client.company_name}")

def send_insomea_po_to_supplier(supplier, po, opportunity):
    """
    Envoyer BC Insomea au fournisseur
    
    ✅ MODIFIÉ: 1 PO = 1 SupplierQuote (plusieurs lignes possibles)
    
    Args:
        supplier: Supplier instance
        po: InsomeaPurchaseOrder instance (contains supplier_quote with lines)
        opportunity: Opportunity instance
    
    Template: emails/insomea_po_to_supplier.html
    """
    
    # ✅ Get lines from supplier_quote
    supplier_quote_lines = po.supplier_quote.lines.all()
    
    context = {
        'supplier': supplier,
        'po': po,
        'lines': supplier_quote_lines,  # ✅ SupplierQuoteLines
        'opportunity': opportunity,
        'total_purchase': po.total_purchase,  # ✅ Calculé depuis property
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
    }
    
    html_message = render_to_string('emails/insomea_po_to_supplier.html', context)
    
    send_mail(
        subject=f"Bon de commande Insomea - {po.po_number}",
        message=f"Bonjour {supplier.name},\n\nVeuillez trouver ci-joint notre bon de commande.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[supplier.email],
        html_message=html_message,
        fail_silently=False,
    )