from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=20, unique=True, db_index=True, verbose_name='Nom')
    display_name = models.CharField(max_length=100, verbose_name='Nom affiché')
    description = models.TextField(blank=True, verbose_name='Description')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rbac_roles'
        verbose_name = 'Rôle'
        verbose_name_plural = 'Rôles'
        ordering = ['name']

    def __str__(self):
        return self.name
