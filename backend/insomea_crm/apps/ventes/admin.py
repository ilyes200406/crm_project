"""
DJANGO ADMIN - APP OPPORTUNITIES

Interface admin pour gestion backend
"""
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Opportunity,
    OpportunityLine,
    SupplierQuote,
    SupplierQuoteLine,
    InsomeaQuote,
    InsomeaQuoteLine,
    ClientPO,
    InsomeaPurchaseOrder,
    Provision,
    Subscription,
    StatusHistory,
)


# ═══════════════════════════════════════════════════════════
# INLINES
# ═══════════════════════════════════════════════════════════

class OpportunityLineInline(admin.TabularInline):
    model = OpportunityLine
    extra = 0
    readonly_fields = ('status', 'created_at')
    fields = ('product', 'quantity', 'billing_cycle', 'status', 'notes')
    can_delete = False


class SupplierQuoteLineInline(admin.TabularInline):
    model = SupplierQuoteLine
    extra = 0
    readonly_fields = ('line_total_purchase',)
    fields = ('opportunity_line', 'unit_price_purchase', 'line_total_purchase', 'sku', 'currency')
    can_delete = False


class InsomeaQuoteLineInline(admin.TabularInline):
    model = InsomeaQuoteLine
    extra = 0
    readonly_fields = ('line_total_purchase', 'line_total_sale', 'line_margin')
    fields = (
        'opportunity_line',
        'supplier_quote_line',
        'unit_price_purchase',
        'line_total_purchase',
        'unit_price_sale',
        'line_total_sale',
        'line_margin',
    )
    can_delete = False


# ═══════════════════════════════════════════════════════════
# OPPORTUNITY ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    
    list_display = (
        'reference',
        'name',
        'client_link',
        'status_badge',
        'assigned_to',
        'lines_count',
        'created_at',
    )
    
    list_filter = ('status', 'created_at', 'assigned_to')
    
    search_fields = ('reference', 'name', 'client__company_name', 'notes')
    
    readonly_fields = (
        'reference',
        'status',
        'created_by',
        'created_at',
        'updated_at',
    )
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('reference', 'name', 'client', 'status')
        }),
        ('Assignation', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('Détails', {
            'fields': ('notes', 'cancellation_reason')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [OpportunityLineInline]
    
    def client_link(self, obj):
        if obj.client:
            url = reverse('admin:clients_client_change', args=[obj.client.id])
            return format_html('<a href="{}">{}</a>', url, obj.client.company_name)
        return '-'
    client_link.short_description = 'Client'
    
    def status_badge(self, obj):
        colors = {
            'DRAFT': 'gray',
            'SUPPLIER_QUOTE_REQUEST': 'blue',
            'SUPPLIER_QUOTE_RECIEVED': 'cyan',
            'INSOMEA_QUOTE_CREATED': 'purple',
            'CLIENT_PO_REQUEST': 'orange',
            'CLIENT_PO_RECIEVED': 'yellow',
            'APPROUVED': 'green',
            'CANCELLED': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def lines_count(self, obj):
        return obj.lines.count()
    lines_count.short_description = 'Lignes'


# ═══════════════════════════════════════════════════════════
# OPPORTUNITY LINE ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(OpportunityLine)
class OpportunityLineAdmin(admin.ModelAdmin):
    
    list_display = (
        'id',
        'opportunity_link',
        'product',
        'quantity',
        'billing_cycle',
        'status_badge',
        'created_at',
    )
    
    list_filter = ('status', 'billing_cycle', 'created_at')
    
    search_fields = (
        'opportunity__reference',
        'product__title',
        'notes'
    )
    
    readonly_fields = ('status', 'created_at', 'updated_at')
    
    def opportunity_link(self, obj):
        url = reverse('admin:opportunities_opportunity_change', args=[obj.opportunity.id])
        return format_html('<a href="{}">{}</a>', url, obj.opportunity.reference)
    opportunity_link.short_description = 'Opportunité'
    
    def status_badge(self, obj):
        colors = {
            'DRAFT': 'gray',
            'SUPPLIER_QUOTE_REQUEST': 'blue',
            'SUPPLIER_QUOTE_RECIEVED': 'green',
            'CANCELLED': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'


# ═══════════════════════════════════════════════════════════
# QUOTE ADMINS
# ═══════════════════════════════════════════════════════════

@admin.register(SupplierQuote)
class SupplierQuoteAdmin(admin.ModelAdmin):
    
    list_display = (
        'reference',
        'supplier',
        'created_by',
        'total_purchase',
        'recieved_at',
    )
    
    list_filter = ('supplier', 'recieved_at')
    
    search_fields = ('reference', 'supplier__name')
    
    readonly_fields = (
        'subtotal_purchase',
        'discount_amount',
        'total_purchase',
        'recieved_at',
    )
    
    inlines = [SupplierQuoteLineInline]


@admin.register(InsomeaQuote)
class InsomeaQuoteAdmin(admin.ModelAdmin):
    
    list_display = (
        'reference',
        'opportunity_link',
        'total_purchase',
        'total_sale',
        'margin',
        'margin_percent',
        'created_at',
    )
    
    list_filter = ('created_at',)
    
    search_fields = ('reference', 'opportunity__reference')
    
    readonly_fields = (
        'reference',
        'subtotal_purchase',
        'total_purchase',
        'subtotal_sale',
        'discount_amount',
        'total_sale',
        'margin',
        'margin_percent',
        'created_at',
    )
    
    inlines = [InsomeaQuoteLineInline]
    
    def opportunity_link(self, obj):
        url = reverse('admin:opportunities_opportunity_change', args=[obj.opportunity.id])
        return format_html('<a href="{}">{}</a>', url, obj.opportunity.reference)
    opportunity_link.short_description = 'Opportunité'


# ═══════════════════════════════════════════════════════════
# PROVISION ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(Provision)
class ProvisionAdmin(admin.ModelAdmin):
    
    list_display = (
        'id',
        'opportunity_line_info',
        'status_badge',
        'provisionned_by',
        'microsoft_subscription_id',
        'provisioning_started_at',
        'provisioning_completed_at',
    )
    
    list_filter = ('status', 'provisionned_by', 'provisioning_started_at')
    
    search_fields = (
        'opportunity_line__opportunity__reference',
        'opportunity_line__product__title',
        'microsoft_subscription_id',
    )
    
    readonly_fields = (
        'status',
        'provisioning_started_at',
        'provisioning_completed_at',
        'created_at',
        'updated_at',
    )
    
    def opportunity_line_info(self, obj):
        return f"{obj.opportunity_line.opportunity.reference} - {obj.opportunity_line.product.title}"
    opportunity_line_info.short_description = 'Ligne'
    
    def status_badge(self, obj):
        colors = {
            'WAITING_PROVISION': 'orange',
            'PROVISIONING': 'blue',
            'PROVISIONED': 'green',
            'ERROR': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    
    list_display = (
        'subscription_number',
        'provision_info',
        'start_date',
        'end_date',
        'is_active_badge',
        'created_at',
    )
    
    list_filter = ('start_date', 'end_date', 'created_at')
    
    search_fields = (
        'subscription_number',
        'provision__opportunity_line__opportunity__reference',
        'provision__opportunity_line__product__title',
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def provision_info(self, obj):
        line = obj.provision.opportunity_line
        return f"{line.opportunity.reference} - {line.product.title}"
    provision_info.short_description = 'Provision'
    
    def is_active_badge(self, obj):
        from datetime import date
        today = date.today()
        is_active = obj.start_date <= today <= obj.end_date
        
        if is_active:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">Actif</span>'
            )
        else:
            return format_html(
                '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">Inactif</span>'
            )
    is_active_badge.short_description = 'Statut'


# ═══════════════════════════════════════════════════════════
# STATUS HISTORY ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    
    list_display = (
        'created_at',
        'entity_type',
        'entity_info',
        'transition_name',
        'status_change',
        'changed_by',
    )
    
    list_filter = ('created_at', 'transition_name', 'changed_by')
    
    search_fields = (
        'opportunity__reference',
        'opportunity_line__product__title',
        'description',
        'transition_name',
    )
    
    readonly_fields = (
        'opportunity',
        'opportunity_line',
        'provision',
        'status_precedent',
        'status_suivant',
        'transition_name',
        'changed_by',
        'description',
        'metadata',
        'ip_address',
        'created_at',
    )
    
    def entity_type(self, obj):
        return obj.get_entity_type()
    entity_type.short_description = 'Type'
    
    def entity_info(self, obj):
        entity = obj.get_entity()
        if obj.opportunity:
            return obj.opportunity.reference
        elif obj.opportunity_line:
            return f"{obj.opportunity_line.opportunity.reference} - {obj.opportunity_line.product.title}"
        elif obj.provision:
            return f"Provision {obj.provision.id}"
        return '-'
    entity_info.short_description = 'Entité'
    
    def status_change(self, obj):
        return format_html(
            '{} <span style="color: gray;">→</span> {}',
            obj.status_precedent,
            obj.status_suivant
        )
    status_change.short_description = 'Changement'
    
    # Read-only admin (pas de modification)
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# Register autres models simples
admin.site.register(ClientPO)
admin.site.register(InsomeaPurchaseOrder)


# ... (garder tout le code existant)

# 🆕 NOUVEAU IMPORT
from .notifications.models import Notification, NotificationType, NotificationStatus
# ═══════════════════════════════════════════════════════════
# 🆕 NOTIFICATION ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    
    list_display = (
        'created_at',
        'type_badge',
        'recipient',
        'title',
        'status_badge',
        'sent_at',
        'read_at',
    )
    
    list_filter = ('type', 'status', 'created_at', 'sent_at')
    
    search_fields = (
        'title',
        'message',
        'recipient__email',
        'recipient__first_name',
        'recipient__last_name',
    )
    
    readonly_fields = (
        'type',
        'recipient',
        'title',
        'message',
        'opportunity',
        'provision',
        'subscription',
        'action_url',
        'status',
        'sent_at',
        'read_at',
        'created_at',
    )
    
    fieldsets = (
        ('Notification', {
            'fields': ('type', 'status', 'recipient')
        }),
        ('Contenu', {
            'fields': ('title', 'message', 'action_url')
        }),
        ('Objets liés', {
            'fields': ('opportunity', 'provision', 'subscription'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('sent_at', 'read_at', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def type_badge(self, obj):
        colors = {
            'FINANCE_APPROVE': '#2196F3',
            'TECH_PROVISION_WAITING': '#FF9800',
            'SUBSCRIPTION_PROVISIONED': '#4CAF50',
            'SUBSCRIPTION_EXPIRING': '#FFC107',
            'SUBSCRIPTION_EXPIRED': '#F44336',
        }
        color = colors.get(obj.type, '#9E9E9E')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_type_display()
        )
    type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#9E9E9E',
            'SENT': '#2196F3',
            'READ': '#4CAF50',
            'FAILED': '#F44336',
        }
        color = colors.get(obj.status, '#9E9E9E')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    # Read-only admin (auto-créées via signals)
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Seulement superuser peut supprimer
"""