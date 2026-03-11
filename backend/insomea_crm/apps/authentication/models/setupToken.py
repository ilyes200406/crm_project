from django.db import models
import secrets
from datetime import timedelta
from ...users.models.users import User
import uuid
from django.utils import timezone
from django.conf import settings

class SetupToken(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='setup_token'
    )
    
    token = models.CharField(max_length=100, unique=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    is_used = models.BooleanField(default=False)
    
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'setup_tokens'
        verbose_name = 'Token de Configuration'
        verbose_name_plural = 'Tokens de Configuration'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Setup token for {self.user.email}"
    
    @classmethod
    def generate_for_user(cls, user):

        cls.objects.filter(user=user).delete()
        
        token = secrets.token_urlsafe(32)

        expires_at = timezone.now() + timedelta(
            hours=settings.SETUP_TOKEN_EXPIRY_HOURS
        )
        
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
    
    def is_valid(self):

        if self.is_used:
            return False
        
        if timezone.now() > self.expires_at:
            return False
        
        return True
    
    def mark_as_used(self):
        now = timezone.now()
        updated = type(self).objects.filter(pk=self.pk, is_used=False).update(
            is_used=True,
            used_at=now
        )
        if updated:
            self.is_used = True
            self.used_at = now
        return bool(updated)