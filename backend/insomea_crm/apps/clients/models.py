"""
EXPLICATION :

Modèles de données pour la gestion clients

Architecture :
- Client : Entité principale (entreprise/personne)
- Contact : Personnes associées au client (composition)
- ClientActivity : Historique des interactions

Design patterns :
- UUID primary keys (sécurité + scalabilité)
- Soft delete (is_active)
- Audit fields (created_at, updated_at, created_by)
- Database indexes (performance)
- Proper constraints (data integrity)
"""

import uuid
from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone
from ..users.models.users import User


# ═══════════════════════════════════════════════════════════
# CHOICES
# ═══════════════════════════════════════════════════════════

class ClientStatus(models.TextChoices):
    """
    Statut du cycle de vie client
    
    LEAD : Prospect identifié (pas encore contacté)
    PROSPECT : Contact établi, qualification en cours
    CUSTOMER : Client actif
    INACTIVE : Client inactif (churn, perdu)
    """
    LEAD = 'LEAD', 'Lead'
    PROSPECT = 'PROSPECT', 'Prospect'
    CUSTOMER = 'CUSTOMER', 'Client'
    INACTIVE = 'INACTIVE', 'Inactif'


class Industry(models.TextChoices):
    """
    Secteurs d'activité principaux (Tunisie)
    
    Explication :
    Liste adaptée au contexte tunisien
    Extensible selon besoins
    """
    IT = 'IT', 'Technologies de l\'information'
    TELECOM = 'TELECOM', 'Télécommunications'
    FINANCE = 'FINANCE', 'Finance et banque'
    MANUFACTURING = 'MANUFACTURING', 'Industrie manufacturière'
    RETAIL = 'RETAIL', 'Commerce et distribution'
    HEALTHCARE = 'HEALTHCARE', 'Santé'
    EDUCATION = 'EDUCATION', 'Éducation'
    GOVERNMENT = 'GOVERNMENT', 'Secteur public'
    ENERGY = 'ENERGY', 'Énergie'
    AGRICULTURE = 'AGRICULTURE', 'Agriculture'
    TOURISM = 'TOURISM', 'Tourisme et hôtellerie'
    TRANSPORT = 'TRANSPORT', 'Transport et logistique'
    OTHER = 'OTHER', 'Autre'


# ═══════════════════════════════════════════════════════════
# CLIENT MODEL
# ═══════════════════════════════════════════════════════════

class Client(models.Model):
    """
    Modèle Client principal
    
    Représente une entreprise ou organisation cliente
    
    Architecture :
    - UUID primary key : Sécurité (impossible à deviner)
    - Soft delete : is_active (pas de suppression physique)
    - Audit fields : who/when
    - Business fields : company info, contact info
    - Relationship fields : assigned_to, created_by
    
    Performance :
    - Indexes sur champs fréquemment filtrés
    - Meta ordering pour requêtes par défaut
    """
    
    # ───────────────────────────────────────────────────────
    # PRIMARY KEY
    # ───────────────────────────────────────────────────────
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    # Explication UUID :
    # - Unique globalement (pas de collision)
    # - Impossible à deviner (sécurité API)
    # - Meilleur pour systèmes distribués
    # - Pas d'enumeration attack (vs auto-increment)
    
    # ───────────────────────────────────────────────────────
    # COMPANY INFORMATION
    # ───────────────────────────────────────────────────────
    
    company_name = models.CharField(
        verbose_name='Raison sociale',
        max_length=255,
        db_index=True  # Index pour recherche rapide
    )
    # Explication db_index=True :
    # Crée un index B-tree
    # → Recherche O(log n) au lieu de O(n)
    # → Essentiel pour WHERE company_name = ...
    
    registration_number = models.CharField(
        verbose_name='Numéro d\'enregistrement',
        max_length=100,
        blank=True,
        null=True,
        help_text='Numéro de registre de commerce ou équivalent'
    )
    
    tax_id = models.CharField(
        verbose_name='Matricule fiscale',
        max_length=100,
        blank=True,
        null=True
    )
    
    industry = models.CharField(
        verbose_name='Secteur d\'activité',
        max_length=50,
        choices=Industry.choices,
        default=Industry.OTHER,
        db_index=True  # Index pour filtrage par secteur
    )
    
    # ───────────────────────────────────────────────────────
    # CONTACT INFORMATION
    # ───────────────────────────────────────────────────────
    
    email = models.EmailField(
        verbose_name='Email principal',
        unique=True,  # Un client = un email unique
        db_index=True  # Index pour recherche rapide
    )
    # Explication unique=True :
    # - Contrainte base de données (data integrity)
    # - Empêche doublons
    # - Crée automatiquement un index unique
    
    phone = models.CharField(
        verbose_name='Téléphone',
        max_length=20,
        blank=True
    )
    
    website = models.URLField(
        verbose_name='Site web',
        blank=True,
        validators=[URLValidator()]
    )
    # Explication URLValidator :
    # - Validation Django built-in
    # - Vérifie format URL valide
    # - Empêche injection de données invalides
    
    # ───────────────────────────────────────────────────────
    # ADDRESS
    # ───────────────────────────────────────────────────────
    
    address = models.TextField(
        verbose_name='Adresse',
        blank=True
    )
    
    city = models.CharField(
        verbose_name='Ville',
        max_length=100,
        blank=True
    )
    
    state = models.CharField(
        verbose_name='Gouvernorat',
        max_length=100,
        blank=True
    )
    
    postal_code = models.CharField(
        verbose_name='Code postal',
        max_length=20,
        blank=True
    )
    
    country = models.CharField(
        verbose_name='Pays',
        max_length=100,
        default='Tunisie',
        db_index=True  # Index pour filtrage par pays
    )
    
    # ───────────────────────────────────────────────────────
    # BUSINESS FIELDS
    # ───────────────────────────────────────────────────────
    
    status = models.CharField(
        verbose_name='Statut',
        max_length=20,
        choices=ClientStatus.choices,
        default=ClientStatus.LEAD,
        db_index=True  # Index CRITIQUE pour filtrage
    )
    # Explication :
    # status est le champ le plus filtré
    # → Index essentiel pour performance
    # WHERE status = 'CUSTOMER' → utilise l'index
    
    tenant_microsoft = models.CharField(
        verbose_name='Tenant Microsoft',
        max_length=255,
        blank=True,
        help_text='Tenant ID Microsoft 365 pour provisioning'
    )
    # Explication :
    # Lien avec système authentication
    # Nécessaire pour provisionnement licences M365
    
    notes = models.TextField(
        verbose_name='Notes',
        blank=True
    )
    
    # ───────────────────────────────────────────────────────
    # RELATIONSHIPS
    # ───────────────────────────────────────────────────────
    
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_clients',
        limit_choices_to={'role': 'COMMERCIAL'},
        db_index=True  # Index pour filtrage par commercial
    )
    # Explication :
    # - SET_NULL : Si commercial supprimé, client reste
    # - related_name : commercial.assigned_clients.all()
    # - limit_choices_to : Seuls commerciaux assignables
    # - db_index : Performance pour "mes clients"
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_clients'
    )
    # Explication :
    # Audit : qui a créé ce client
    # SET_NULL : garde l'historique même si user supprimé
    
    # ───────────────────────────────────────────────────────
    # SOFT DELETE
    # ───────────────────────────────────────────────────────
    
    is_active = models.BooleanField(
        verbose_name='Actif',
        default=True,
        db_index=True  # Index pour filtrage actifs/inactifs
    )
    # Explication soft delete :
    # - Pas de DELETE FROM clients
    # - UPDATE clients SET is_active = False
    # - Garde historique complet
    # - Récupération possible
    # - Contraintes référentielles intactes
    
    # ───────────────────────────────────────────────────────
    # TIMESTAMPS
    # ───────────────────────────────────────────────────────
    
    created_at = models.DateTimeField(
        verbose_name='Date de création',
        auto_now_add=True,
        db_index=True  # Index pour tri chronologique
    )
    # Explication auto_now_add :
    # - Set automatiquement à la création
    # - Immutable (ne change jamais)
    
    updated_at = models.DateTimeField(
        verbose_name='Dernière modification',
        auto_now=True
    )
    # Explication auto_now :
    # - Update automatiquement à chaque save()
    # - Audit des modifications
    
    # ───────────────────────────────────────────────────────
    # META
    # ───────────────────────────────────────────────────────
    
    class Meta:
        db_table = 'clients'
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['-created_at']  # Par défaut : plus récents d'abord
        
        indexes = [
            # Indexes composites pour requêtes fréquentes
            models.Index(
                fields=['status', 'is_active'],
                name='idx_client_status_active'
            ),
            # Explication index composite :
            # WHERE status = 'CUSTOMER' AND is_active = True
            # → Utilise cet index composite
            # → Plus rapide que 2 index séparés
            
            models.Index(
                fields=['assigned_to', 'is_active'],
                name='idx_client_assigned_active'
            ),
            # Explication :
            # "Mes clients actifs" → requête très fréquente
            # Index optimisé pour ce cas
            
            models.Index(
                fields=['created_at'],
                name='idx_client_created'
            ),
            # Explication :
            # Tri chronologique fréquent
            # ORDER BY created_at DESC
        ]
        
        constraints = [
            # Constraint unique conditionnelle
            models.UniqueConstraint(
                fields=['email'],
                condition=models.Q(is_active=True),
                name='unique_active_client_email'
            ),
            # Explication :
            # Email unique SEULEMENT pour clients actifs
            # Permet réutilisation email si client désactivé
        ]
    
    # ───────────────────────────────────────────────────────
    # METHODS
    # ───────────────────────────────────────────────────────
    
    def __str__(self):
        return f"{self.company_name} ({self.get_status_display()})"
    
    def soft_delete(self):
        """
        Soft delete : désactive au lieu de supprimer
        
        Explication :
        - UPDATE au lieu de DELETE
        - Garde toutes les relations intactes
        - Audit trail complet
        """
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
    
    def restore(self):
        """Restaure un client désactivé"""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])
    
    def assign_to_user(self, user):
        """
        Assigne le client à un commercial
        
        Validation :
        - User doit être COMMERCIAL
        """
        if user.role != 'COMMERCIAL':
            raise ValueError('Seuls les commerciaux peuvent être assignés')
        
        self.assigned_to = user
        self.save(update_fields=['assigned_to', 'updated_at'])


# ═══════════════════════════════════════════════════════════
# CONTACT MODEL
# ═══════════════════════════════════════════════════════════

class Contact(models.Model):
    """
    Contact associé à un client
    
    Explication :
    - Relation de composition avec Client
    - Un client peut avoir plusieurs contacts
    - Un contact principal (est_principal=True)
    
    Use case :
    - Client = "Dupont SA"
    - Contacts = ["Jean Dupont (CEO)", "Marie Dubois (CTO)"]
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,  # Suppression client → suppression contacts
        related_name='contacts'
    )
    # Explication CASCADE :
    # Si client supprimé (soft delete), contacts restent
    # Mais si vraie suppression (admin), contacts supprimés
    
    first_name = models.CharField(
        verbose_name='Prénom',
        max_length=150
    )
    
    last_name = models.CharField(
        verbose_name='Nom',
        max_length=150
    )
    
    position = models.CharField(
        verbose_name='Poste',
        max_length=150,
        blank=True
    )
    
    email = models.EmailField(
        verbose_name='Email',
        db_index=True
    )
    
    phone = models.CharField(
        verbose_name='Téléphone',
        max_length=20,
        blank=True
    )
    
    mobile = models.CharField(
        verbose_name='Mobile',
        max_length=20,
        blank=True
    )
    
    is_primary = models.BooleanField(
        verbose_name='Contact principal',
        default=False
    )
    # Explication :
    # Un seul contact principal par client
    # Validation dans services.py
    
    notes = models.TextField(
        verbose_name='Notes',
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contacts'
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        ordering = ['-is_primary', 'last_name', 'first_name']
        # Explication ordering :
        # Contact principal en premier
        # Puis alphabétique par nom
        
        indexes = [
            models.Index(fields=['client', 'is_primary'], name='idx_contact_client_primary'),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.client.company_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


# ═══════════════════════════════════════════════════════════
# CLIENT ACTIVITY MODEL
# ═══════════════════════════════════════════════════════════

class ClientActivity(models.Model):
    """
    Historique des interactions avec le client
    
    Explication :
    - Log de toutes les activités
    - Qui a fait quoi, quand
    - Intégration avec système d'audit
    
    Types d'activités :
    - CLIENT_CREATED, CLIENT_UPDATED, CLIENT_DELETED
    - CLIENT_VIEWED, CLIENT_ASSIGNED
    - CLIENT_CONTACTED, CLIENT_MEETING
    - NOTE_ADDED, QUOTE_SENT, etc.
    """
    
    class ActivityType(models.TextChoices):
        CREATED = 'CREATED', 'Créé'
        UPDATED = 'UPDATED', 'Modifié'
        DELETED = 'DELETED', 'Supprimé'
        RESTORED = 'RESTORED', 'Restauré'
        VIEWED = 'VIEWED', 'Consulté'
        ASSIGNED = 'ASSIGNED', 'Assigné'
        STATUS_CHANGED = 'STATUS_CHANGED', 'Statut changé'
        CONTACTED = 'CONTACTED', 'Contacté'
        MEETING = 'MEETING', 'Réunion'
        NOTE_ADDED = 'NOTE_ADDED', 'Note ajoutée'
        EMAIL_SENT = 'EMAIL_SENT', 'Email envoyé'
        CALL_MADE = 'CALL_MADE', 'Appel effectué'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    
    activity_type = models.CharField(
        verbose_name='Type d\'activité',
        max_length=50,
        choices=ActivityType.choices,
        db_index=True
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='client_activities'
    )
    # Explication :
    # Qui a effectué l'action
    # SET_NULL : garde historique même si user supprimé
    
    description = models.TextField(
        verbose_name='Description',
        blank=True
    )
    
    metadata = models.JSONField(
        verbose_name='Métadonnées',
        default=dict,
        blank=True
    )
    # Explication JSONField :
    # Stocke données structurées additionnelles
    # Ex: {"old_status": "LEAD", "new_status": "PROSPECT"}
    
    ip_address = models.GenericIPAddressField(
        verbose_name='Adresse IP',
        null=True,
        blank=True
    )
    # Explication :
    # Audit : d'où vient l'action
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'client_activities'
        verbose_name = 'Activité client'
        verbose_name_plural = 'Activités clients'
        ordering = ['-created_at']
        
        indexes = [
            models.Index(
                fields=['client', 'created_at'],
                name='idx_activity_client_date'
            ),
            models.Index(
                fields=['activity_type', 'created_at'],
                name='idx_activity_type_date'
            ),
        ]
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.client.company_name} - {self.created_at}"