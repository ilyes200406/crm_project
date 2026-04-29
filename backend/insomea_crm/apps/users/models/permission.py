from django.db import models


class Permission(models.Model):
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
    role = models.ForeignKey(
        'Role',
        on_delete=models.CASCADE,
        to_field='name',
        db_column='role_name',
        related_name='role_permissions',
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
        return f"{self.role_id} → {self.permission.codename}"
