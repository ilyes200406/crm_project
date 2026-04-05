"""
WEBSOCKET MIDDLEWARE

JWT Authentication pour WebSocket
"""

from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT Authentication Middleware pour WebSocket
    
    Extrait le token JWT du query string et authentifie l'utilisateur
    
    Usage:
        ws://localhost:8000/ws/notifications/?token=<jwt_token>
    """
    
    async def __call__(self, scope, receive, send):
        # Parse query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        # Get token from query params
        token = query_params.get('token', [None])[0]
        
        # Authenticate user
        scope['user'] = await self.get_user_from_token(token)
        
        return await super().__call__(scope, receive, send)
    
    @database_sync_to_async
    def get_user_from_token(self, token):
        """
        Get user from JWT token
        
        Args:
            token: JWT access token
        
        Returns:
            User instance or AnonymousUser
        """
        
        if not token:
            return AnonymousUser()
        
        try:
            # Decode token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # Get user
            user = User.objects.get(id=user_id)
            return user
        
        except (InvalidToken, TokenError, User.DoesNotExist):
            return AnonymousUser()