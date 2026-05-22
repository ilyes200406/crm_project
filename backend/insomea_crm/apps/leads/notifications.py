from apps.ventes.notifications.models import Notification, NotificationType
from apps.ventes.notifications.services import send_notification_to_websocket, send_notification_email


def notify_nouveau_lead(demande):
    """
    Notifie tous les commerciaux et admins d'une nouvelle demande.
    Appelé après soumission publique du formulaire.
    """
    from apps.users.models import User

    recipients = User.objects.filter(role_id__in=['COMMERCIAL', 'ADMIN'], is_active=True)

    for user in recipients:
        notification = Notification.objects.create(
            type=NotificationType.NOUVEAU_LEAD,
            recipient=user,
            title=f"Nouvelle demande — {demande.nom_entreprise}",
            message=(
                f"{demande.nom_contact} ({demande.email}) a soumis une demande. "
                f"Produits : {demande.produits_suggeres or 'Non précisé'}."
            ),
            action_url=f"/leads/{demande.id}/",
        )
        try:
            send_notification_to_websocket(notification)
            send_notification_email(notification)
            notification.mark_as_sent()
        except Exception:
            notification.mark_as_failed()
