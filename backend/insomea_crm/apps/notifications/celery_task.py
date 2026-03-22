# apps/notifications/tasks.py - VERSION COMPLÈTE ET TESTÉE
from celery import shared_task
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Notification
from apps.deploiements.models import Attribution
from .email_service import send_email
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task
def verifier_echeances():
    """
    CRON QUOTIDIEN - 8h00 tous les jours
    Vérifie toutes les attributions actives et envoie alertes
    """
    logger.info('='*50)
    logger.info('[CRON] DÉBUT vérification échéances')
    logger.info(f'[CRON] Date/Heure: {datetime.now()}')
    logger.info('='*50)
    
    today = datetime.now().date()
    niveaux_alerte = [90, 60, 30, 7]
    
    stats = {
        'total_attributions': 0,
        'alertes_envoyees': 0,
        'emails_envoyes': 0,
        'erreurs': 0
    }
    
    try:
        # Récupérer toutes les attributions actives
        attributions = Attribution.objects.filter(
            statut='ACTIVE'
        ).select_related(
            'client',
            'produit',
            'commercial'
        ).prefetch_related(
            'deploiement'
        )
        
        stats['total_attributions'] = attributions.count()
        logger.info(f"[CRON] {stats['total_attributions']} attributions actives trouvées")
        
        for attribution in attributions:
            try:
                # Calculer jours restants
                jours_restants = (attribution.date_fin - today).days
                
                # Log pour debug
                if jours_restants <= 90:
                    logger.debug(
                        f"[CRON] Attribution {attribution.id[:8]} "
                        f"({attribution.client.raison_sociale} - {attribution.produit.nom}): "
                        f"{jours_restants} jours restants"
                    )
                
                # Si correspond à un niveau d'alerte
                if jours_restants in niveaux_alerte:
                    logger.info(
                        f"[CRON] ⚠️ ALERTE J-{jours_restants} : "
                        f"{attribution.client.raison_sociale} - {attribution.produit.nom}"
                    )
                    
                    # Vérifier si alerte déjà envoyée aujourd'hui (éviter doublons)
                    alerte_existe = Notification.objects.filter(
                        attribution=attribution,
                        type=f'EXPIR_{jours_restants}J',
                        date_envoi__date=today
                    ).exists()
                    
                    if alerte_existe:
                        logger.debug(f"[CRON] Alerte déjà envoyée aujourd'hui, skip")
                        continue
                    
                    # Créer notification
                    notification = Notification.objects.create(
                        attribution=attribution,
                        destinataire=attribution.commercial,
                        type=f'EXPIR_{jours_restants}J',
                        titre=f'Attribution expire dans {jours_restants} jours',
                        message=(
                            f"Client: {attribution.client.raison_sociale}\n"
                            f"Produit: {attribution.produit.nom}\n"
                            f"Quantité: {attribution.quantite}\n"
                            f"Date expiration: {attribution.date_fin.strftime('%d/%m/%Y')}"
                        ),
                        canal='LES_DEUX'
                    )
                    stats['alertes_envoyees'] += 1
                    
                    # Déterminer urgence
                    if jours_restants <= 7:
                        urgence = 'CRITIQUE'
                    elif jours_restants <= 30:
                        urgence = 'HAUTE'
                    else:
                        urgence = 'NORMALE'
                    
                    # Envoyer email
                    email_sent = send_email(
                        to=attribution.commercial.email,
                        subject=f'⚠️ Attribution expire dans {jours_restants} jours',
                        template='alerte_expiration',
                        context={
                            'commercial': attribution.commercial.first_name,
                            'client': attribution.client.raison_sociale,
                            'produit': attribution.produit.nom,
                            'quantite': attribution.quantite,
                            'date_expiration': attribution.date_fin.strftime('%d/%m/%Y'),
                            'jours_restants': jours_restants,
                            'urgence': urgence,
                            'frontend_url': settings.FRONTEND_URL,
                            'attribution_id': str(attribution.id)
                        }
                    )
                    
                    if email_sent:
                        stats['emails_envoyes'] += 1
                    
            except Exception as e:
                logger.error(f"[CRON] Erreur traitement attribution {attribution.id}: {str(e)}")
                stats['erreurs'] += 1
                continue
        
        # Log final
        logger.info('='*50)
        logger.info('[CRON] FIN vérification échéances')
        logger.info(f"[CRON] Statistiques:")
        logger.info(f"[CRON]   - Attributions vérifiées: {stats['total_attributions']}")
        logger.info(f"[CRON]   - Alertes créées: {stats['alertes_envoyees']}")
        logger.info(f"[CRON]   - Emails envoyés: {stats['emails_envoyes']}")
        logger.info(f"[CRON]   - Erreurs: {stats['erreurs']}")
        logger.info('='*50)
        
        return stats
        
    except Exception as e:
        logger.error(f"[CRON] ERREUR CRITIQUE: {str(e)}")
        raise

@shared_task
def test_cron_manuel():
    """Tâche de test pour vérifier que Celery fonctionne"""
    logger.info('[TEST] Celery fonctionne correctement !')
    return {'status': 'OK', 'timestamp': str(datetime.now())}