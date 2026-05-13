from celery import shared_task


@shared_task(
    name='users.tasks.send_setup_email_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_setup_email_task(self, user_id, setup_url, created_by_id=None):
    from .models.users import User
    from ..authentication.emails import send_setup_email

    user = User.objects.get(id=user_id)
    try:
        send_setup_email(user, setup_url)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            _notify_setup_email_failure(user, created_by_id)
        raise self.retry(exc=exc)


def _notify_setup_email_failure(user, created_by_id=None):
    from .models.users import User
    from ..ventes.notifications.models import Notification, NotificationType
    from ..ventes.notifications.services import send_notification_to_websocket

    recipients = set()
    if created_by_id:
        try:
            recipients.add(User.objects.get(id=created_by_id))
        except User.DoesNotExist:
            pass
    recipients.update(User.objects.filter(role_id='ADMIN', is_active=True))

    for admin in recipients:
        notification = Notification.objects.create(
            type=NotificationType.EMAIL_FAILED,
            recipient=admin,
            title=f"Échec email invitation – {user.email}",
            message=(
                f"Impossible d'envoyer l'email d'invitation à {user.email} "
                f"après 3 tentatives. Utilisez l'action « Renvoyer l'invitation » "
                f"depuis la liste des utilisateurs."
            ),
            action_url=f"/admin/users/user/{user.id}/change/",
        )
        try:
            send_notification_to_websocket(notification)
            notification.mark_as_sent()
        except Exception:
            notification.mark_as_failed()
