

"""
# ═══════════════════════════════════════════════════════════
# STATUS HISTORY
# ═══════════════════════════════════════════════════════════

class StatusHistorySerializer(serializers.ModelSerializer):

    #Serializer StatusHistory (audit trail)
    
    #Usage:
    #    GET (nested dans OpportunityDetailSerializer)
    #    GET /status-history/
 
    
    changed_by = UserMinimalSerializer(read_only=True)
    entity_type = serializers.CharField(source='get_entity_type', read_only=True)
    entity = serializers.SerializerMethodField()
    
    class Meta:
        model = StatusHistory
        fields = [
            'id',
            'entity_type',
            'entity',
            'status_precedent',
            'status_suivant',
            'transition_name',
            'description',
            'metadata',
            'changed_by',
            'ip_address',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_entity(self, obj):
        #Retourne référence entité concernée
        entity = obj.get_entity()
        
        if not entity:
            return None
        
        # Retourne infos minimales selon type
        if obj.opportunity_line:
            return {
                'id': str(obj.opportunity_line.id),
                'product': obj.opportunity_line.product.title if obj.opportunity_line.product else None,
            }
        elif obj.opportunity:
            return {
                'id': str(obj.opportunity.id),
                'reference': obj.opportunity.reference,
                'name': obj.opportunity.name,
            }
        elif obj.provision:
            return {
                'id': str(obj.provision.id),
                'opportunity_line_id': str(obj.provision.opportunity_line_id),
            }
        
        return None
"""