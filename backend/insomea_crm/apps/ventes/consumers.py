"""
WEBSOCKET CONSUMERS

Consumer pour notifications real-time
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer pour notifications
    
    Channel name: notifications_{user_id}
    
    Messages:
        - notification.send: Nouvelle notification
        - notification.read: Notification lue
        - notification.count: Update count
    
    Usage Frontend:
        ws://localhost:8000/ws/notifications/
    """
    
    async def connect(self):
        """
        Connection WebSocket
        
        Flow:
            1. User authenticate via JWT (query param)
            2. Join personal channel: notifications_{user_id}
            3. Send initial count
        """
        
        # Get user from scope (AuthMiddleware)
        self.user = self.scope.get('user')
        
        # Check authentication
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Channel name: notifications_{user_id}
        self.room_group_name = f'notifications_{self.user.id}'
        
        # Join channel
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept connection
        await self.accept()
        
        # Send initial unread count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'notification.count',
            'count': unread_count
        }))
    
    async def disconnect(self, close_code):
        """Disconnect WebSocket"""
        
        if hasattr(self, 'room_group_name'):
            # Leave channel
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket
        
        Messages supportés:
            - {"action": "mark_read", "notification_id": "uuid"}
            - {"action": "get_count"}
        """
        
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'mark_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)
                    
                    # Send updated count
                    unread_count = await self.get_unread_count()
                    await self.send(text_data=json.dumps({
                        'type': 'notification.count',
                        'count': unread_count
                    }))
            
            elif action == 'get_count':
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'notification.count',
                    'count': unread_count
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    # ───────────────────────────────────────────────────────
    # CHANNEL LAYER HANDLERS
    # ───────────────────────────────────────────────────────
    
    async def notification_send(self, event):
        """
        Handler: Nouvelle notification
        
        Triggered by: channel_layer.group_send()
        
        Event data:
            {
                'type': 'notification.send',
                'notification': {...}
            }
        """
        
        # Send to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification.new',
            'notification': event['notification']
        }))
    
    async def notification_count(self, event):
        """
        Handler: Update count
        
        Event data:
            {
                'type': 'notification.count',
                'count': 5
            }
        """
        
        await self.send(text_data=json.dumps({
            'type': 'notification.count',
            'count': event['count']
        }))
    
    # ───────────────────────────────────────────────────────
    # DATABASE HELPERS
    # ───────────────────────────────────────────────────────
    
    @database_sync_to_async
    def get_unread_count(self):
        """Get unread notifications count"""
        from .notifications.models import Notification, NotificationStatus
        
        return Notification.objects.filter(
            recipient=self.user,
            status=NotificationStatus.PENDING
        ).count()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        from .notifications.models import Notification
        
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            notification.mark_as_read()
        except Notification.DoesNotExist:
            pass