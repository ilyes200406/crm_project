from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta
from django.conf import settings
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(verbose_name='Adresse email', max_length=255, unique=True, db_index=True)

    first_name = models.CharField(verbose_name='Prénom', max_length=150, blank=True)
    last_name = models.CharField(verbose_name='Nom', max_length=150, blank=True)
    role = models.ForeignKey('Role', on_delete=models.PROTECT, related_name='users', to_field='name', db_column='role_name', verbose_name='Rôle',)

    is_active = models.BooleanField(verbose_name='Actif', default=False)
    is_verified = models.BooleanField(verbose_name='Email vérifié', default=False)
    is_staff = models.BooleanField(verbose_name='Staff', default=False)

    date_joined = models.DateTimeField(verbose_name="Date d'inscription", default=timezone.now)
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

    def has_ventes_perm(self, codename: str) -> bool:
        if self.role_id == 'ADMIN':
            return True
        from .permission import RolePermission
        return RolePermission.objects.filter(
            role_id=self.role_id,
            permission__codename=codename
        ).exists()
