"""
EXPLICATION :

Ce fichier contient TOUS les modèles de données pour l'authentification :
1. Utilisateur : Custom user avec rôle
2. SetupToken : Token pour configuration compte (24h)
3. PasswordResetToken : Token pour reset password (1h)
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid
import secrets
from datetime import timedelta
from django.conf import settings
from .managers import UserManager


class RoleChoices(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrateur'
    COMMERCIAL = 'COMMERCIAL', 'Commercial'
    TECHNICIEN = 'TECHNICIEN', 'Technicien'
    FINANCE = 'FINANCE', 'Finance'


class User(AbstractBaseUser, PermissionsMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(verbose_name='Adresse email', max_length=255, unique=True, db_index=True)

    first_name = models.CharField(verbose_name='Prénom', max_length=150, blank=True)
    last_name = models.CharField(verbose_name='Nom', max_length=150, blank=True)
    role = models.CharField(verbose_name='Rôle', max_length=20, choices=RoleChoices.choices, default=RoleChoices.COMMERCIAL)

    is_active = models.BooleanField(verbose_name='Actif', default=False)
    is_verified = models.BooleanField(verbose_name='Email vérifié', default=False)
    is_staff = models.BooleanField(verbose_name='Staff', default=False)

    date_joined = models.DateTimeField(verbose_name='Date d\'inscription', default=timezone.now)  
    last_login = models.DateTimeField(verbose_name='Dernière connexion', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    
    REQUIRED_FIELDS = ['role']

    class Meta:
        db_table = 'utilisateurs'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.email
    
    def get_short_name(self):
        return self.first_name if self.first_name else self.email

    # ── Role helpers ───────────────────────────────────────────────────────
    # Convenience checks used across services and templates.

    def is_admin(self):
        return self.role == RoleChoices.ADMIN

    def is_commercial(self):
        return self.role == RoleChoices.COMMERCIAL

    def is_technicien(self):
        return self.role == RoleChoices.TECHNICIEN

    def is_finance(self):
        return self.role == RoleChoices.FINANCE

    # ── RBAC Layer 1 ───────────────────────────────────────────────────────

    def has_ventes_perm(self, codename: str) -> bool:
        """
        Layer 1 + Layer 3 combined check.

        ADMIN always returns True — no DB query, maximum performance.
        Any other role: looks up RolePermission to see if that role has
        the requested codename assigned.

        Usage:
            user.has_ventes_perm('opportunity.create')   → True/False
            user.has_ventes_perm('opportunity.approve')  → True only for FINANCE/ADMIN

        Called by HasVentesPerm.has_permission() in users/permissions.py.
        """
        if self.role == RoleChoices.ADMIN:
            return True
        from .permission import RolePermission
        return RolePermission.objects.filter(
            role=self.role,
            permission__codename=codename
        ).exists()







