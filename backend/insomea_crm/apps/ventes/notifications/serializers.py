"""
NOTIFICATION SERIALIZER
"""

from rest_framework import serializers
from .models import Notification, NotificationType


# Maps backend type → frontend dot notation + level
_TYPE_CONFIG = {
    NotificationType.FINANCE_APPROVE: {
        'notification_type': 'finance.approval_required',
        'level': 'warning',
    },
    NotificationType.TECH_PROVISION_WAITING: {
        'notification_type': 'provision.created',
        'level': 'info',
    },
    NotificationType.SUBSCRIPTION_PROVISIONED: {
        'notification_type': 'provision.completed',
        'level': 'success',
    },
    NotificationType.SUBSCRIPTION_EXPIRING: {
        'notification_type': 'subscription.expiring_soon',
        'level': 'warning',
    },
    NotificationType.SUBSCRIPTION_EXPIRED: {
        'notification_type': 'subscription.cancelled',
        'level': 'error',
    },
}


class NotificationSerializer(serializers.ModelSerializer):

    is_read = serializers.SerializerMethodField()
    notification_type = serializers.SerializerMethodField()
    related_object_id = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'related_object_id',
            'level',
            'is_read',
            'action_url',
            'created_at',
        ]
        read_only_fields = fields

    def get_is_read(self, obj):
        return obj.is_read

    def get_notification_type(self, obj):
        config = _TYPE_CONFIG.get(obj.type, {})
        return config.get('notification_type', 'info')

    def get_level(self, obj):
        config = _TYPE_CONFIG.get(obj.type, {})
        return config.get('level', 'info')

    def get_related_object_id(self, obj):
        # Return the most relevant FK id based on type
        if obj.type in (NotificationType.FINANCE_APPROVE,) and obj.opportunity_id:
            return str(obj.opportunity_id)
        if obj.type in (NotificationType.TECH_PROVISION_WAITING, NotificationType.SUBSCRIPTION_PROVISIONED) and obj.provision_id:
            return str(obj.provision_id)
        if obj.type in (NotificationType.SUBSCRIPTION_EXPIRING, NotificationType.SUBSCRIPTION_EXPIRED) and obj.subscription_id:
            return str(obj.subscription_id)
        # Fallback: first non-null FK
        return str(obj.opportunity_id or obj.provision_id or obj.subscription_id or '')
