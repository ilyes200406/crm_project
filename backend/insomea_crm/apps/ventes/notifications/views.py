"""
NOTIFICATION VIEWS
"""

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification, NotificationStatus
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = Notification.objects.filter(
            recipient=self.request.user
        ).select_related('opportunity', 'provision', 'subscription')

        if self.request.query_params.get('unread_only') == 'true':
            qs = qs.exclude(status=NotificationStatus.READ)

        return qs

    # ── custom actions ──────────────────────────────────────

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        Notification.objects.filter(
            recipient=request.user,
        ).exclude(
            status=NotificationStatus.READ
        ).update(
            status=NotificationStatus.READ,
            read_at=timezone.now(),
        )
        return Response({'status': 'ok'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            status__in=[NotificationStatus.PENDING, NotificationStatus.SENT],
        ).count()
        return Response({'count': count})
