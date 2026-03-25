"""
ADMIN - APP SUPPLIERS

Interface Django Admin pour gestion suppliers
"""
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import Supplier, SupplierType


# ═══════════════════════════════════════════════════════════
# SUPPLIER ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    # ───────────────────────────────────────────────────────
    # LIST DISPLAY
    # ───────────────────────────────────────────────────────
    
    list_display = [
        'name',
        'type_badge',
        'support_email',
        'support_phone',
        'is_active_badge',
        'created_at',
    ]
    
    list_display_links = ['name']
    
    # ───────────────────────────────────────────────────────
    # FILTERS
    # ───────────────────────────────────────────────────────
    
    list_filter = [
        'type',
        'is_active',
        'created_at',
    ]
    
    # ───────────────────────────────────────────────────────
    # SEARCH
    # ───────────────────────────────────────────────────────
    
    search_fields = [
        'name',
        'support_email',
        'notes',
    ]
    
    # ───────────────────────────────────────────────────────
    # FIELDSETS
    # ───────────────────────────────────────────────────────
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': (
                'name',
                'type',
            )
        }),
        (_('Contact'), {
            'fields': (
                'website',
                'support_email',
                'support_phone',
            )
        }),
        (_('Notes internes'), {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
        (_('Statut'), {
            'fields': ('is_active',),
        }),
        (_('Métadonnées'), {
            'fields': (
                'id',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # ───────────────────────────────────────────────────────
    # READ-ONLY FIELDS
    # ───────────────────────────────────────────────────────
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]
    
    # ───────────────────────────────────────────────────────
    # ORDERING
    # ───────────────────────────────────────────────────────
    
    ordering = ['name']
    
    # ───────────────────────────────────────────────────────
    # ACTIONS
    # ───────────────────────────────────────────────────────
    
    actions = [
        'activate_suppliers',
        'deactivate_suppliers',
        'export_csv',
    ]
    
    # ───────────────────────────────────────────────────────
    # CUSTOM DISPLAY METHODS
    # ───────────────────────────────────────────────────────
    
    @admin.display(description='Type', ordering='type')
    def type_badge(self, obj):
        colors = {
            SupplierType.DIRECT: '#2563eb',      # Bleu
            SupplierType.DISTRIBUTOR: '#16a34a', # Vert
            SupplierType.RESELLER: '#ea580c',    # Orange
        }
        
        color = colors.get(obj.type, '#6b7280')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_type_display()
        )
    
    @admin.display(description='Actif', boolean=True, ordering='is_active')
    def is_active_badge(self, obj):
        return obj.is_active
    
    # ───────────────────────────────────────────────────────
    # BULK ACTIONS
    # ───────────────────────────────────────────────────────
    
    @admin.action(description='Activer les fournisseurs sélectionnés')
    def activate_suppliers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} fournisseur(s) activé(s) avec succès.'
        )
    
    @admin.action(description='Désactiver les fournisseurs sélectionnés')
    def deactivate_suppliers(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} fournisseur(s) désactivé(s) avec succès.'
        )
    
    @admin.action(description='Exporter en CSV')
    def export_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="suppliers.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID',
            'Nom',
            'Type',
            'Site web',
            'Email support',
            'Téléphone support',
            'Actif',
            'Date création',
        ])
        
        for supplier in queryset:
            writer.writerow([
                str(supplier.id),
                supplier.name,
                supplier.get_type_display(),
                supplier.website,
                supplier.support_email,
                supplier.support_phone,
                'Oui' if supplier.is_active else 'Non',
                supplier.created_at.strftime('%Y-%m-%d %H:%M'),
            ])
        
        return response
    
    # ───────────────────────────────────────────────────────
    # QUERYSET OPTIMIZATION
    # ───────────────────────────────────────────────────────
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Pas de select_related nécessaire (pas de FK)
        return qs
"""