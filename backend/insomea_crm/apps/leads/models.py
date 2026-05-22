import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class StatutDemande(models.TextChoices):
    NOUVELLE = 'NOUVELLE', _('Nouvelle')
    PRISE_EN_CHARGE = 'PRISE_EN_CHARGE', _('Prise en charge')
    CONVERTIE = 'CONVERTIE', _('Convertie')
    ANNULEE = 'ANNULEE', _('Annulée')


class DemandeClient(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    nom_entreprise = models.CharField(max_length=200)
    nom_contact = models.CharField(max_length=200)
    email = models.EmailField()
    telephone = models.CharField(max_length=20, blank=True)
    message = models.TextField()
    produits_suggeres = models.TextField(blank=True)

    statut = models.CharField(
        max_length=20,
        choices=StatutDemande.choices,
        default=StatutDemande.NOUVELLE,
    )
    prise_en_charge_par = models.ForeignKey(
        'users.User',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='demandes_prises_en_charge',
    )
    prise_en_charge_at = models.DateTimeField(null=True, blank=True)

    # Lien optionnel quand la demande devient une opportunité
    opportunite = models.ForeignKey(
        'ventes.Opportunity',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='demande_source',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'leads_demandes'
        ordering = ['-created_at']
        verbose_name = 'Demande client'
        verbose_name_plural = 'Demandes clients'

        indexes = [
            models.Index(fields=['statut', '-created_at']),
            models.Index(fields=['prise_en_charge_par', 'statut']),
        ]

    def __str__(self):
        return f"{self.nom_entreprise} — {self.get_statut_display()}"
