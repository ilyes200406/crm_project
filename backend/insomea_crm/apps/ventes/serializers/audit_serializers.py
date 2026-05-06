from rest_framework import serializers

from ..models import StatusHistory


class StatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()
    entity_type = serializers.SerializerMethodField()

    class Meta:
        model = StatusHistory
        fields = [
            'id',
            'entity_type',
            'status_precedent',
            'status_suivant',
            'transition_name',
            'changed_by_name',
            'description',
            'metadata',
            'ip_address',
            'created_at',
        ]
        read_only_fields = fields

    def get_changed_by_name(self, obj):
        if obj.changed_by:
            return getattr(obj.changed_by, 'get_full_name', lambda: str(obj.changed_by))() or str(obj.changed_by)
        return 'system'

    def get_entity_type(self, obj):
        return obj.get_entity_type()
