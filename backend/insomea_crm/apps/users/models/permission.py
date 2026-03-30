"""
RBAC PERMISSION MODELS

Two tables form the heart of the three-layer authorization system:

  Permission      — a named action ("opportunity.create", "provision.start", …)
  RolePermission  — which role is allowed to perform that action

WHY TWO SEPARATE TABLES instead of a hardcoded dict?
  - You can change role capabilities at runtime (Django admin, management command)
    without touching code or redeploying.
  - A single source of truth: instead of the same role list scattered across
    10+ files, one query answers "can this role do X?".
  - Auditable: you can log/inspect what permissions exist and who has them.

HOW IT FITS THE THREE-LAYER MODEL:
  Layer 1 (RBAC)     → User.has_ventes_perm(codename) queries RolePermission
  Layer 2 (Ownership)→ _is_owner(user, obj) in users/permissions.py
  Layer 3 (Admin)    → ADMIN bypasses everything, no DB query needed
"""

from django.db import models
from .users import RoleChoices


class Permission(models.Model):
    """
    One row = one named action that can be performed in the system.

    codename  — machine-readable identifier, used in code (e.g. 'opportunity.create')
    name      — human-readable label shown in Django admin

    Example rows after seeding:
        codename='opportunity.create',   name='Créer une opportunité'
        codename='opportunity.approve',  name='Approuver une opportunité'
        codename='provision.start',      name='Démarrer le provisionnement'
    """

    codename = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='Code',
        help_text="Identifiant machine (ex: 'opportunity.create')"
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Nom',
        help_text="Label lisible (ex: 'Créer une opportunité')"
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description',
        help_text='Contexte optionnel sur ce que cette permission autorise'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rbac_permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['codename']

    def __str__(self):
        return self.codename


class RolePermission(models.Model):
    """
    One row = "role X is allowed to do permission Y".

    This is the mapping table that answers:
        "Can a COMMERCIAL user create an opportunity?" → look for
        (role='COMMERCIAL', permission__codename='opportunity.create')

    Example rows after seeding:
        role='COMMERCIAL', permission → 'opportunity.create'
        role='FINANCE',    permission → 'opportunity.approve'
        role='TECHNICIEN', permission → 'provision.start'

    ADMIN role is NOT seeded here — it bypasses this table entirely
    (Layer 3 override in has_ventes_perm()).
    """

    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        db_index=True,
        verbose_name='Rôle'
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='role_permissions',
        verbose_name='Permission'
    )

    class Meta:
        db_table = 'rbac_role_permissions'
        verbose_name = 'Permission par rôle'
        verbose_name_plural = 'Permissions par rôle'
        unique_together = ['role', 'permission']
        indexes = [
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.role} → {self.permission.codename}"
