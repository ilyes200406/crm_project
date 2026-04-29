"""
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

class Industry(models.TextChoices):
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

class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_clients', limit_choices_to={'role_id': 'COMMERCIAL'}, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_clients')

    company_name = models.CharField(verbose_name='Raison sociale', max_length=255, db_index=True)
    industry = models.CharField(verbose_name='Secteur d\'activité', max_length=50, choices=Industry.choices, default=Industry.OTHER, db_index=True)
    email = models.EmailField(verbose_name='Email principal', unique=True, db_index=True)
    phone = models.CharField(verbose_name='Téléphone', max_length=20, blank=True) 
    website = models.URLField(verbose_name='Site web', blank=True, validators=[URLValidator()])
    address = models.TextField(verbose_name='Adresse', blank=True)
    tenant_microsoft = models.CharField(verbose_name='Tenant Microsoft', max_length=255, blank=True)
    notes = models.TextField(verbose_name='Notes', blank=True)

    is_active = models.BooleanField(verbose_name='Actif', default=True, db_index=True)
    created_at = models.DateTimeField(verbose_name='Date de création', auto_now_add=True, db_index=True) 
    updated_at = models.DateTimeField(verbose_name='Dernière modification', auto_now=True)
    
    class Meta:
        db_table = 'clients'
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['-created_at']  # Par défaut : plus récents d'abord
        
        indexes = [
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
        ]
    
    def __str__(self):
        return self.company_name
    
    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
    
    def restore(self):
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])
    
    def assign_to_user(self, user):
        if user.role_id != 'COMMERCIAL':
            raise ValueError('Seuls les commerciaux peuvent être assignés')
        
        self.assigned_to = user
        self.save(update_fields=['assigned_to', 'updated_at'])


class Contact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    
    first_name = models.CharField(verbose_name='Prénom', max_length=150)
    last_name = models.CharField(verbose_name='Nom', max_length=150)
    position = models.CharField(verbose_name='Poste', max_length=150, blank=True)
    email = models.EmailField(verbose_name='Email', db_index=True)
    phone = models.CharField(verbose_name='Téléphone', max_length=20, blank=True)
    is_primary = models.BooleanField(verbose_name='Contact principal', default=False)
    
    notes = models.TextField(verbose_name='Notes', blank=True)
    
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


class ClientActivity(models.Model):
    class ActivityType(models.TextChoices):
        CREATED  = 'CREATED',  'Créé'
        UPDATED  = 'UPDATED',  'Modifié'
        DELETED  = 'DELETED',  'Désactivé'
        RESTORED = 'RESTORED', 'Réactivé'
        ASSIGNED = 'ASSIGNED', 'Réassigné'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='client_activities')
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'client_activities'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.activity_type} — {self.client.company_name}"