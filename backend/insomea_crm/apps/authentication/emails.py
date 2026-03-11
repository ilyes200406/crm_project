from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_setup_email(user, setup_url):
    context = {
        'user': user,
        'setup_url': setup_url,
        'expiry_hours': settings.SETUP_TOKEN_EXPIRY_HOURS,
    }
    
    # Render HTML
    html_message = render_to_string('emails/setup_account.html', context)
    
    # Version texte (fallback)
    plain_message = strip_tags(html_message)
    
    # Envoie email
    send_mail(
        subject='Configurez votre compte Insomea',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(user, reset_url):
    context = {
        'user': user,
        'reset_url': reset_url,
        'expiry_hours': settings.PASSWORD_RESET_TOKEN_EXPIRY_HOURS,
    }
    
    html_message = render_to_string('emails/password_reset.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Réinitialisation de votre mot de passe',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )