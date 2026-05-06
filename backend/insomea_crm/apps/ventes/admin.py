"""
DJANGO ADMIN - APP VENTES

Interface admin complète pour tester le workflow CRM de bout en bout :
Opportunity → SupplierQuote → InsomeaQuote → ClientPO → Approve
→ InsomeaPOs envoyés → InsomeaPOs confirmés → Provisions créées
→ Start/Complete provisioning → Subscription + SubscriptionTerm créés
"""

from django import forms
from django.contrib import admin
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

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
    StatusHistory,
    Subscription,
    SubscriptionStatus,
    SubscriptionTerm,
)


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _status_badge(value, display, colors):
    color = colors.get(value, '#9E9E9E')
    return format_html(
        '<span style="background-color:{}; color:white; padding:3px 10px; '
        'border-radius:3px; font-size:11px; font-weight:bold;">{}</span>',
        color, display
    )


OPPORTUNITY_STATUS_COLORS = {
    'DRAFT': '#9E9E9E',
    'SUPPLIER_QUOTE_REQUEST': '#2196F3',
    'SUPPLIER_QUOTE_RECIEVED': '#00BCD4',
    'INSOMEA_QUOTE_CREATED': '#9C27B0',
    'CLIENT_PO_REQUEST': '#FF9800',
    'CLIENT_PO_RECIEVED': '#FFC107',
    'APPROUVED': '#4CAF50',
    'INSOMEA_POS_SENT': '#8BC34A',
    'INSOMEA_POS_CONFIRMED': '#009688',
    'CANCELLED': '#F44336',
}

PROVISION_STATUS_COLORS = {
    'WAITING_PROVISION': '#FF9800',
    'PROVISIONING': '#2196F3',
    'PROVISIONED': '#4CAF50',
    'ERROR': '#F44336',
}


# ═══════════════════════════════════════════════════════════
# INLINES
# ═══════════════════════════════════════════════════════════

class StatusHistoryInline(admin.TabularInline):
    model = StatusHistory
    extra = 0
    readonly_fields = (
        'created_at', 'transition_name', 'status_precedent',
        'status_suivant', 'changed_by', 'ip_address', 'description',
    )
    fields = (
        'created_at', 'transition_name', 'status_precedent',
        'status_suivant', 'changed_by', 'ip_address', 'description',
    )
    can_delete = False
    ordering = ('-created_at',)
    show_change_link = False

    def has_add_permission(self, request, obj=None):
        return False


class OpportunityLineInline(admin.TabularInline):
    model = OpportunityLine
    extra = 1
    readonly_fields = ('status', 'created_at')
    fields = ('product', 'quantity', 'billing_cycle', 'status', 'notes')
    can_delete = True
    show_change_link = True


class SupplierQuoteLineInline(admin.TabularInline):
    model = SupplierQuoteLine
    extra = 1
    readonly_fields = ('line_total_purchase',)
    fields = ('opportunity_line', 'unit_price_purchase', 'line_total_purchase', 'sku', 'currency', 'delivery_time')
    can_delete = False


class InsomeaQuoteLineInline(admin.TabularInline):
    model = InsomeaQuoteLine
    extra = 1
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


class SubscriptionTermInline(admin.TabularInline):
    model = SubscriptionTerm
    extra = 0
    readonly_fields = ('total_purchase', 'total_sale', 'created_at')
    fields = (
        'term_number', 'start_date', 'end_date',
        'unit_price_purchase', 'unit_price_sale',
        'total_purchase', 'total_sale',
    )
    can_delete = False


# ═══════════════════════════════════════════════════════════
# INTERMEDIATE FORM — Complete Provisioning
# ═══════════════════════════════════════════════════════════

class CompleteProvisioningForm(forms.Form):
    subscription_number = forms.CharField(
        max_length=200,
        label="Numéro de subscription Microsoft",
        help_text="Ex: SUB-2024-00001  (laisser vide si renewal)",
        required=False,
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date de début",
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date de fin",
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        if start and end and end <= start:
            raise forms.ValidationError("La date de fin doit être après la date de début.")
        return cleaned


# ═══════════════════════════════════════════════════════════
# OPPORTUNITY ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):

    list_display = (
        'reference',
        'name',
        'client',
        'type',
        'status_badge',
        'assigned_to',
        'lines_count',
        'created_at',
    )

    list_filter = ('status', 'type', 'created_at', 'assigned_to')

    search_fields = ('reference', 'name', 'client__company_name', 'notes')

    readonly_fields = (
        'id',
        'reference',
        'status',
        'created_by',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (_('Informations générales'), {
            'fields': ('id', 'reference', 'name', 'client', 'type', 'related_opportunity', 'status')
        }),
        (_('Assignation'), {
            'fields': ('created_by', 'assigned_to', 'approved_by')
        }),
        (_('Détails'), {
            'fields': ('notes', 'cancellation_reason')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [OpportunityLineInline, StatusHistoryInline]

    actions = [
        'action_request_supplier_quotes',
        'action_approve',
        'action_confirm_all_pos',
        'action_cancel',
    ]

    # ─── Display methods ────────────────────────────────────

    @admin.display(description='Statut', ordering='status')
    def status_badge(self, obj):
        return _status_badge(obj.status, obj.get_status_display(), OPPORTUNITY_STATUS_COLORS)

    @admin.display(description='Lignes')
    def lines_count(self, obj):
        return obj.lines.count()

    # ─── Workflow actions ────────────────────────────────────

    @admin.action(description='① Demander devis fournisseurs (DRAFT → SUPPLIER_QUOTE_REQUEST)')
    def action_request_supplier_quotes(self, request, queryset):
        from .services import request_all_supplier_quotes
        ok = 0
        for opp in queryset:
            try:
                request_all_supplier_quotes(opportunity_id=opp.id, user=request.user)
                ok += 1
            except Exception as e:
                self.message_user(request, f"[{opp.reference}] Erreur : {e}", level='error')
        if ok:
            self.message_user(request, f'{ok} opportunité(s) → devis fournisseurs demandés.')

    @admin.action(description='⑦ Approuver + envoyer BCs Insomea (CLIENT_PO_RECIEVED → APPROUVED → INSOMEA_POS_SENT)')
    def action_approve(self, request, queryset):
        from .services import approve_opportunity
        ok = 0
        for opp in queryset:
            try:
                approve_opportunity(opportunity_id=opp.id, user=request.user)
                ok += 1
            except Exception as e:
                self.message_user(request, f"[{opp.reference}] Erreur : {e}", level='error')
        if ok:
            self.message_user(request, f'{ok} opportunité(s) approuvée(s) et BCs Insomea envoyés.')

    @admin.action(description='⑧ Confirmer tous les BCs Insomea → crée les Provisions')
    def action_confirm_all_pos(self, request, queryset):
        from .services import confirm_all_insomea_pos
        ok = 0
        for opp in queryset:
            try:
                confirm_all_insomea_pos(opportunity_id=opp.id, user=request.user)
                ok += 1
            except Exception as e:
                self.message_user(request, f"[{opp.reference}] Erreur : {e}", level='error')
        if ok:
            self.message_user(request, f'{ok} opportunité(s) : BCs Insomea confirmés + Provisions créées.')

    @admin.action(description='✖ Annuler les opportunités sélectionnées')
    def action_cancel(self, request, queryset):
        cancelled = 0
        for opp in queryset:
            try:
                opp.cancel(reason='Annulation via admin')
                opp.save()
                cancelled += 1
            except Exception as e:
                self.message_user(request, f"[{opp.reference}] Erreur : {e}", level='error')
        if cancelled:
            self.message_user(request, f'{cancelled} opportunité(s) annulée(s).')

    
    @admin.action(description='⑤ Demander le BC client (INSOMEA_QUOTE_CREATED → CLIENT_PO_REQUEST)')
    def action_request_client_po(self, request, queryset):
        ok = 0
        for opp in queryset:
            try:
                opp.request_client_po()
                opp.save()
                ok += 1
            except Exception as e:
                self.message_user(request, f"[{opp.reference}] Erreur : {e}", level='error')
        if ok:
            self.message_user(request, f'{ok} opportunité(s) → BC client demandé.')


# ═══════════════════════════════════════════════════════════
# OPPORTUNITY LINE ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(OpportunityLine)
class OpportunityLineAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'opportunity',
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
        'notes',
    )

    readonly_fields = ('id', 'status', 'created_at', 'updated_at')

    fieldsets = (
        (_('Ligne'), {
            'fields': ('id', 'opportunity', 'product', 'quantity', 'billing_cycle', 'status')
        }),
        (_('Renouvellement'), {
            'fields': ('renewal_of_subscription', 'insomea_purchase_order'),
            'classes': ('collapse',)
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Statut', ordering='status')
    def status_badge(self, obj):
        colors = {
            'DRAFT': '#9E9E9E',
            'SUPPLIER_QUOTE_REQUEST': '#2196F3',
            'SUPPLIER_QUOTE_RECIEVED': '#4CAF50',
            'INSOMEA_PO_SENT': '#FF9800',
            'INSOMEA_PO_CONFIRMED': '#009688',
            'CANCELLED': '#F44336',
        }
        return _status_badge(obj.status, obj.get_status_display(), colors)


# ═══════════════════════════════════════════════════════════
# SUPPLIER QUOTE ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(SupplierQuote)
class SupplierQuoteAdmin(admin.ModelAdmin):

    list_display = (
        'reference',
        'supplier',
        'created_by',
        'total_purchase',
        'discount_percent',
        'recieved_at',
    )

    list_filter = ('supplier', 'recieved_at')

    search_fields = ('reference', 'supplier__name')

    readonly_fields = (
        'id',
        'reference',
        'subtotal_purchase',
        'discount_amount',
        'total_purchase',
        'recieved_at',
    )

    fieldsets = (
        (_('Devis fournisseur'), {
            'fields': ('id', 'reference', 'supplier', 'created_by', 'document')
        }),
        (_('Remise'), {
            'fields': ('discount_percent',)
        }),
        (_('Totaux (calculés)'), {
            'fields': ('subtotal_purchase', 'discount_amount', 'total_purchase'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('recieved_at',),
            'classes': ('collapse',)
        }),
    )

    inlines = [SupplierQuoteLineInline]


# ═══════════════════════════════════════════════════════════
# INSOMEA QUOTE ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(InsomeaQuote)
class InsomeaQuoteAdmin(admin.ModelAdmin):

    list_display = (
        'reference',
        'opportunity',
        'created_by',
        'total_purchase',
        'total_sale',
        'margin',
        'margin_percent',
        'created_at',
    )

    list_filter = ('created_at',)

    search_fields = ('reference', 'opportunity__reference')

    readonly_fields = (
        'id',
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

    fieldsets = (
        (_('Devis Insomea'), {
            'fields': ('id', 'reference', 'opportunity', 'created_by', 'document')
        }),
        (_('Remise'), {
            'fields': ('discount_percent',)
        }),
        (_('Totaux achat (calculés)'), {
            'fields': ('subtotal_purchase', 'total_purchase'),
            'classes': ('collapse',)
        }),
        (_('Totaux vente + marge (calculés)'), {
            'fields': ('subtotal_sale', 'discount_amount', 'total_sale', 'margin', 'margin_percent'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    inlines = [InsomeaQuoteLineInline]


# ═══════════════════════════════════════════════════════════
# CLIENT PO ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(ClientPO)
class ClientPOAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'opportunity',
        'po_number',
        'created_by',
        'recieved_at',
    )

    list_filter = ('recieved_at',)

    search_fields = ('opportunity__reference', 'po_number')

    readonly_fields = ('id', 'recieved_at')

    fieldsets = (
        (_('BC Client'), {
            'fields': ('id', 'opportunity', 'created_by', 'po_number', 'document')
        }),
        (_('Métadonnées'), {
            'fields': ('recieved_at',),
            'classes': ('collapse',)
        }),
    )


# ═══════════════════════════════════════════════════════════
# INSOMEA PURCHASE ORDER ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(InsomeaPurchaseOrder)
class InsomeaPurchaseOrderAdmin(admin.ModelAdmin):

    list_display = (
        'po_number',
        'supplier',
        'created_by',
        'sent_at',
        'confirmed_at',
        'created_at',
    )

    list_filter = ('supplier', 'sent_at', 'confirmed_at')

    search_fields = ('po_number', 'supplier__name')

    readonly_fields = ('id', 'created_at')

    fieldsets = (
        (_('BC Insomea'), {
            'fields': ('id', 'po_number', 'supplier', 'supplier_quote', 'created_by', 'document')
        }),
        (_('Suivi'), {
            'fields': ('sent_at', 'confirmed_at')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


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
        'id',
        'status',
        'provisioning_started_at',
        'provisioning_completed_at',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (_('Provision'), {
            'fields': ('id', 'opportunity_line', 'status', 'provisionned_by')
        }),
        (_('Subscription liée'), {
            'fields': ('subscription', 'subscription_term', 'microsoft_subscription_id')
        }),
        (_('Dates provisionnement'), {
            'fields': ('provisioning_started_at', 'provisioning_completed_at', 'provisioning_error')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['action_start_provisioning', 'action_complete_provisioning', 'action_fail_provisioning']

    # ─── Display methods ────────────────────────────────────

    @admin.display(description='Ligne')
    def opportunity_line_info(self, obj):
        return f"{obj.opportunity_line.opportunity.reference} — {obj.opportunity_line.product.title}"

    @admin.display(description='Statut', ordering='status')
    def status_badge(self, obj):
        return _status_badge(obj.status, obj.get_status_display(), PROVISION_STATUS_COLORS)

    # ─── Workflow actions ────────────────────────────────────

    @admin.action(description='⑨ Démarrer le provisionnement (WAITING → PROVISIONING)')
    def action_start_provisioning(self, request, queryset):
        from .services import start_provisioning
        ok = 0
        for provision in queryset:
            try:
                start_provisioning(provision_id=provision.id, user=request.user)
                ok += 1
            except Exception as e:
                self.message_user(request, f"[{provision.id}] Erreur : {e}", level='error')
        if ok:
            self.message_user(request, f'{ok} provision(s) démarrée(s).')

    @admin.action(description='⑩ Terminer le provisionnement → crée Subscription + SubscriptionTerm')
    def action_complete_provisioning(self, request, queryset):
        from .services import complete_provisioning

        if 'apply' in request.POST:
            form = CompleteProvisioningForm(request.POST)
            if form.is_valid():
                ok = 0
                for provision in queryset:
                    try:
                        complete_provisioning(
                            provision_id=provision.id,
                            subscription_data=form.cleaned_data,
                            user=request.user,
                        )
                        ok += 1
                    except Exception as e:
                        self.message_user(request, f"[{provision.id}] Erreur : {e}", level='error')
                if ok:
                    self.message_user(request, f'{ok} provision(s) terminée(s) — Subscriptions créées.')
                return None
        else:
            form = CompleteProvisioningForm()

        return TemplateResponse(
            request,
            'admin/ventes/complete_provisioning.html',
            {
                'title': 'Terminer le provisionnement',
                'form': form,
                'queryset': queryset,
                'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
                'opts': self.model._meta,
            },
        )

    @admin.action(description='✖ Marquer le provisionnement en erreur')
    def action_fail_provisioning(self, request, queryset):
        from .services import fail_provisioning
        ok = 0
        for provision in queryset:
            try:
                fail_provisioning(
                    provision_id=provision.id,
                    error_message='Échec manuel via admin',
                    user=request.user,
                )
                ok += 1
            except Exception as e:
                self.message_user(request, f"[{provision.id}] Erreur : {e}", level='error')
        if ok:
            self.message_user(request, f'{ok} provision(s) marquée(s) en erreur.')


# ═══════════════════════════════════════════════════════════
# SUBSCRIPTION ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):

    list_display = (
        'subscription_number',
        'client',
        'product',
        'quantity',
        'billing_cycle',
        'current_term_start',
        'current_term_end',
        'status_badge',
        'auto_renew',
        'created_at',
    )

    list_filter = ('status', 'billing_cycle', 'auto_renew', 'created_at')

    search_fields = (
        'subscription_number',
        'client__company_name',
        'product__title',
    )

    readonly_fields = ('id', 'status', 'created_at', 'updated_at')

    fieldsets = (
        (_('Subscription'), {
            'fields': ('id', 'subscription_number', 'client', 'product', 'quantity', 'billing_cycle', 'status')
        }),
        (_('Période courante'), {
            'fields': ('current_term_start', 'current_term_end', 'auto_renew')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [SubscriptionTermInline]

    actions = ['action_mark_pending_renewal']

    @admin.action(description='[Dev] Mark selected as PENDING_RENEWAL')
    def action_mark_pending_renewal(self, request, queryset):
        count = 0
        for sub in queryset.filter(status=SubscriptionStatus.ACTIVE):
            sub.mark_pending_renewal()
            sub.save(update_fields=['status'])
            count += 1
        self.message_user(request, f'{count} subscription(s) marked as PENDING_RENEWAL.')

    @admin.display(description='Statut', ordering='status')
    def status_badge(self, obj):
        colors = {
            'ACTIVE': '#4CAF50',
            'PENDING_RENEWAL': '#FF9800',
            'EXPIRED': '#9E9E9E',
            'CANCELLED': '#F44336',
        }
        return _status_badge(obj.status, obj.get_status_display(), colors)


# ═══════════════════════════════════════════════════════════
# SUBSCRIPTION TERM ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(SubscriptionTerm)
class SubscriptionTermAdmin(admin.ModelAdmin):

    list_display = (
        'subscription',
        'term_number',
        'start_date',
        'end_date',
        'unit_price_purchase',
        'unit_price_sale',
        'total_purchase',
        'total_sale',
        'created_at',
    )

    list_filter = ('start_date', 'end_date')

    search_fields = (
        'subscription__subscription_number',
        'subscription__client__company_name',
        'subscription__product__title',
    )

    readonly_fields = ('id', 'total_purchase', 'total_sale', 'created_at', 'updated_at')

    fieldsets = (
        (_('Terme'), {
            'fields': ('id', 'subscription', 'opportunity', 'term_number', 'start_date', 'end_date', 'auto_renew_enabled')
        }),
        (_('Prix'), {
            'fields': ('unit_price_purchase', 'unit_price_sale', 'total_purchase', 'total_sale')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ═══════════════════════════════════════════════════════════
# STATUS HISTORY ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):

    list_display = (
        'created_at',
        'entity_type_display',
        'transition_name',
        'status_precedent',
        'status_suivant',
        'changed_by',
        'ip_address',
    )

    list_filter = ('transition_name', 'created_at')

    search_fields = (
        'transition_name',
        'description',
        'changed_by__email',
        'opportunity__reference',
    )

    readonly_fields = (
        'id', 'opportunity', 'opportunity_line', 'provision', 'subscription',
        'status_precedent', 'status_suivant', 'transition_name',
        'changed_by', 'description', 'metadata', 'ip_address', 'created_at',
    )

    fieldsets = (
        (_('Entité'), {
            'fields': ('id', 'opportunity', 'opportunity_line', 'provision', 'subscription')
        }),
        (_('Transition'), {
            'fields': ('transition_name', 'status_precedent', 'status_suivant')
        }),
        (_('Contexte'), {
            'fields': ('changed_by', 'ip_address', 'description', 'metadata')
        }),
        (_('Horodatage'), {
            'fields': ('created_at',)
        }),
    )

    ordering = ('-created_at',)

    @admin.display(description='Type entité')
    def entity_type_display(self, obj):
        return obj.get_entity_type() or '—'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ═══════════════════════════════════════════════════════════
# NOTIFICATION ADMIN
# ═══════════════════════════════════════════════════════════

try:
    from .notifications.models import Notification, NotificationType, NotificationStatus

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

        list_filter = ('type', 'status', 'created_at')

        search_fields = (
            'title',
            'message',
            'recipient__email',
        )

        readonly_fields = (
            'type', 'recipient', 'title', 'message',
            'opportunity', 'provision', 'subscription',
            'action_url', 'status', 'sent_at', 'read_at', 'created_at',
        )

        fieldsets = (
            (_('Notification'), {
                'fields': ('type', 'status', 'recipient')
            }),
            (_('Contenu'), {
                'fields': ('title', 'message', 'action_url')
            }),
            (_('Objets liés'), {
                'fields': ('opportunity', 'provision', 'subscription'),
                'classes': ('collapse',)
            }),
            (_('Métadonnées'), {
                'fields': ('sent_at', 'read_at', 'created_at'),
                'classes': ('collapse',)
            }),
        )

        @admin.display(description='Type')
        def type_badge(self, obj):
            colors = {
                'FINANCE_APPROVE': '#2196F3',
                'TECH_PROVISION_WAITING': '#FF9800',
                'SUBSCRIPTION_PROVISIONED': '#4CAF50',
                'SUBSCRIPTION_EXPIRING': '#FFC107',
                'SUBSCRIPTION_EXPIRED': '#F44336',
            }
            return _status_badge(obj.type, obj.get_type_display(), colors)

        @admin.display(description='Statut')
        def status_badge(self, obj):
            colors = {
                'PENDING': '#9E9E9E',
                'SENT': '#2196F3',
                'READ': '#4CAF50',
                'FAILED': '#F44336',
            }
            return _status_badge(obj.status, obj.get_status_display(), colors)

        def has_add_permission(self, request):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return request.user.is_superuser

except ImportError:
    pass




