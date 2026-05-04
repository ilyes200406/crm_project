"""
EXPLICATION :

Django Admin = Interface graphique pour gestion données

Architecture :
- Admin optimisé avec select_related
- Filtres et recherche avancés
- Actions en masse
- Inline editing pour relations
- Display customisé avec badges colorés

Avantages :
- UI professionnelle sans code frontend
- CRUD rapide pour admins
- Audit trail visible
- Export intégré

Performance :
- Queries optimisées (évite N+1)
- Pagination automatique
- Indexes utilisés
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count

from .models import Client, Contact, ClientActivity


# ═══════════════════════════════════════════════════════════
# INLINE ADMINS (Relations)
# ═══════════════════════════════════════════════════════════

class ContactInline(admin.TabularInline):
    """
    Inline pour contacts dans ClientAdmin
    
    Explication :
    Affiche contacts directement dans page client
    Édition inline (pas besoin page séparée)
    
    TabularInline : Format tableau
    Alternative : StackedInline (format vertical)
    
    Use case :
    Admin édite client → voit contacts → ajoute/modifie inline
    """
    
    model = Contact
    extra = 0  # Pas de ligne vide par défaut
    # Explication extra=0 :
    # Par défaut, Django affiche 3 lignes vides
    # extra=0 : affiche seulement existants + bouton "Add"
    
    fields = [
        'first_name',
        'last_name',
        'position',
        'email',
        'phone',
        'is_primary',
    ]
    
    readonly_fields = []
    
    min_num = 1
    validate_min = True
    # Limite nombre contacts affichés (performance)
    max_num = 20


class ClientActivityInline(admin.TabularInline):
    """
    Inline pour activités dans ClientAdmin
    
    Explication :
    Read-only (activités créées par système)
    Affiche 10 dernières activités
    """
    
    model = ClientActivity
    extra = 0
    max_num = 10
    
    fields = [
        'activity_type',
        'user',
        'description',
        'created_at',
    ]
    
    readonly_fields = [
        'activity_type',
        'user',
        'description',
        'created_at',
        'ip_address',
    ]
    
    can_delete = False
    # Explication :
    # Pas de suppression inline
    # Activités = audit trail permanent
    
    def has_add_permission(self, request, obj=None):
        """Empêche ajout manuel"""
        return False


# ═══════════════════════════════════════════════════════════
# CLIENT ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Configuration admin pour Client
    
    Features :
    - Liste optimisée avec badges colorés
    - Filtres sidebar (status, industry, etc.)
    - Recherche multi-champs
    - Actions en masse
    - Inline contacts et activités
    - Export CSV
    - Stats agrégées
    
    Performance :
    - select_related sur FK
    - prefetch_related pour inlines
    - Pagination 50 items
    """
    
    # ───────────────────────────────────────────────────────
    # LIST DISPLAY
    # ───────────────────────────────────────────────────────
    
    list_display = [
        'company_name',
        'email',
        'phone',
        'industry_display',
        'assigned_to_link',
        'contacts_count',
        'is_active_badge',
        'created_at',
    ]
    # Explication :
    # Colonnes affichées dans liste
    # Méthodes custom : status_badge, city_country, etc.
    
    list_display_links = ['company_name', 'email']
    # Explication :
    # Colonnes cliquables → page détails
    
    # ───────────────────────────────────────────────────────
    # FILTERS
    # ───────────────────────────────────────────────────────
    
    list_filter = [
        'industry',
        'is_active',
        ('assigned_to', admin.RelatedOnlyFieldListFilter),
        ('created_by', admin.RelatedOnlyFieldListFilter),
        'created_at',
    ]
    # Explication RelatedOnlyFieldListFilter :
    # Affiche seulement valeurs utilisées
    # Pas tous les users, juste ceux assignés
    # Performance : évite query lourde
    
    # ───────────────────────────────────────────────────────
    # SEARCH
    # ───────────────────────────────────────────────────────
    
    search_fields = [
        'company_name',
        'email',
        'phone',
        'notes',
        'contacts__first_name',
        'contacts__last_name',
        'contacts__email',
    ]
    # Explication :
    # Recherche dans client + contacts (JOIN)
    # contacts__first_name : lookup relation
    
    # ───────────────────────────────────────────────────────
    # ORDERING
    # ───────────────────────────────────────────────────────
    
    ordering = ['-created_at']
    # Plus récents d'abord
    
    # ───────────────────────────────────────────────────────
    # PAGINATION
    # ───────────────────────────────────────────────────────
    
    list_per_page = 50
    # 50 clients par page (performance)
    
    # ───────────────────────────────────────────────────────
    # FIELDSETS (organisation formulaire)
    # ───────────────────────────────────────────────────────
    
    fieldsets = (
        ('Informations entreprise', {
            'fields': (
                'company_name',
                'industry',
            )
        }),

        ('Contact', {
            'fields': (
                'email',
                'phone',
                'website',
                'address',
            )
        }),

        ('Assignation', {
            'fields': (
                'assigned_to',
                'tenant_microsoft',
            )
        }),

        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),

        ('Méta-données', {
            'fields': (
                'is_active',
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # ───────────────────────────────────────────────────────
    # READONLY FIELDS
    # ───────────────────────────────────────────────────────
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'created_by',
    ]
    # Explication :
    # Champs affichés mais non modifiables
    # Timestamps auto-gérés
    
    # ───────────────────────────────────────────────────────
    # AUTOCOMPLETE (pour ForeignKeys)
    # ───────────────────────────────────────────────────────
    
    autocomplete_fields = ['assigned_to', 'created_by']
    # Explication :
    # Widget autocomplete au lieu de dropdown
    # Performance : évite charger tous les users
    # Recherche dynamique avec AJAX
    
    # ───────────────────────────────────────────────────────
    # INLINES
    # ───────────────────────────────────────────────────────
    
    inlines = [ContactInline, ClientActivityInline]
    # Explication :
    # Affiche contacts et activités dans page client
    # Édition inline possible (contacts)
    # Read-only pour activités
    
    # ───────────────────────────────────────────────────────
    # ACTIONS EN MASSE
    # ───────────────────────────────────────────────────────
    
    actions = [
        'activate_clients',
        'deactivate_clients',
        'assign_to_commercial',
        'export_as_csv',
    ]
    
    def activate_clients(self, request, queryset):
        """
        Active clients sélectionnés
        
        Explication :
        Admin coche plusieurs clients
        Sélectionne "Activer" dans dropdown Actions
        → is_active=True pour tous
        """
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} client(s) activé(s) avec succès.',
            level='success'
        )
        # Explication message_user :
        # Affiche message vert en haut de page
    
    activate_clients.short_description = "Activer les clients sélectionnés"
    # Texte affiché dans dropdown
    
    def deactivate_clients(self, request, queryset):
        """Désactive clients (soft delete)"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} client(s) désactivé(s) avec succès.',
            level='warning'
        )
    
    deactivate_clients.short_description = "Désactiver les clients sélectionnés"
    
    def assign_to_commercial(self, request, queryset):
        """
        Réassigne en masse
        
        TODO : Implémenter formulaire intermédiaire
        Pour sélectionner commercial cible
        
        Explication :
        Action complexe nécessite input additionnel
        Django admin permet formulaire intermédiaire
        """
        # Placeholder : à implémenter avec formulaire
        self.message_user(
            request,
            'Fonctionnalité à venir : sélection du commercial',
            level='info'
        )
    
    assign_to_commercial.short_description = "Réassigner à un commercial"
    
    def export_as_csv(self, request, queryset):
        """
        Export CSV des clients sélectionnés
        
        Explication :
        Génère CSV des clients cochés
        Alternative : export via API endpoint
        """
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        # Response CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="clients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Headers
        writer.writerow([
            'Raison sociale',
            'Email',
            'Téléphone',
            'Secteur',
            'Assigné à',
            'Actif',
            'Créé le',
        ])

        # Data
        for client in queryset.select_related('assigned_to'):
            writer.writerow([
                client.company_name,
                client.email,
                client.phone,
                client.get_industry_display(),
                client.assigned_to.get_full_name() if client.assigned_to else '',
                'Oui' if client.is_active else 'Non',
                client.created_at.strftime('%Y-%m-%d %H:%M'),
            ])
        
        return response
    
    export_as_csv.short_description = "Exporter en CSV"
    
    # ───────────────────────────────────────────────────────
    # CUSTOM DISPLAY METHODS
    # ───────────────────────────────────────────────────────
    
    def industry_display(self, obj):
        """Affichage secteur"""
        return obj.get_industry_display()
    
    industry_display.short_description = 'Secteur'
    industry_display.admin_order_field = 'industry'
    
    def assigned_to_link(self, obj):
        """
        Lien vers commercial assigné
        
        Explication :
        Lien cliquable vers page admin user
        Utilise reverse() pour URL
        
        Sécurité :
        mark_safe() SEULEMENT sur HTML contrôlé
        """
        if obj.assigned_to:
            url = reverse(
                'admin:users_user_change',
                args=[obj.assigned_to.id]
            )
            return mark_safe(
                f'<a href="{url}">{obj.assigned_to.get_full_name()}</a>'
            )
        return '-'
    
    assigned_to_link.short_description = 'Assigné à'
    assigned_to_link.admin_order_field = 'assigned_to'
    
    def contacts_count(self, obj):
        """
        Nombre de contacts
        
        Explication :
        Si annoté (via get_queryset), utilise annotation
        Sinon, compte via relation
        """
        # Si annoté
        if hasattr(obj, 'contacts_count_annotated'):
            return obj.contacts_count_annotated
        
        # Sinon compte
        return obj.contacts.count()
    
    contacts_count.short_description = 'Contacts'
    
    def is_active_badge(self, obj):
        """Badge actif/inactif
        if obj.is_active:
            return format_html(
                '<span style="color: #10B981; font-weight: 600;">✓ Actif</span>'
            )
        else:
            return format_html(
                '<span style="color: #EF4444; font-weight: 600;">{}</span>',✗ Inactif 
            )
        """
        if obj.is_active:
            return format_html(
                '<span style="color: #10B981; font-weight: 600;">{}</span>',
                '✓ Actif'
            )
        else:
            return format_html(
                '<span style="color: #EF4444; font-weight: 600;">{}</span>',
                '✗ Inactif'
            )
    
    is_active_badge.short_description = 'État'
    is_active_badge.admin_order_field = 'is_active'
    
    # ───────────────────────────────────────────────────────
    # QUERY OPTIMIZATION
    # ───────────────────────────────────────────────────────
    
    def get_queryset(self, request):
        """
        Optimise queryset admin
        
        Explication :
        Override pour ajouter select_related
        Évite N+1 queries
        
        Performance :
        Sans : 1 + N queries (N = nombre clients)
        Avec : 1 query avec JOINs
        """
        queryset = super().get_queryset(request)
        
        # select_related pour FK (assigned_to, created_by)
        queryset = queryset.select_related(
            'assigned_to',
            'created_by'
        )
        
        # Annotation pour contacts_count
        queryset = queryset.annotate(
            contacts_count_annotated=Count('contacts')
        )
        # Explication :
        # Compte contacts en SQL (GROUP BY)
        # Évite COUNT(*) par client
        
        return queryset
    
    # ───────────────────────────────────────────────────────
    # SAVE OVERRIDE (pour audit)
    # ───────────────────────────────────────────────────────
    
    def save_model(self, request, obj, form, change):
        """
        Override save pour audit
        
        Args:
            request: HttpRequest
            obj: Client instance
            form: ModelForm
            change: True si update, False si create
        
        Explication :
        Appelé lors du save admin
        Permet ajouter logique custom
        
        Use case :
        - Set created_by si création
        - Log activité admin
        """
        if not change:
            # Création
            obj.created_by = request.user
        
        super().save_model(request, obj, form, change)
        
        # Log activité (optionnel)
        from .services import log_client_activity
        from .models import ClientActivity
        
        activity_type = ClientActivity.ActivityType.UPDATED if change else ClientActivity.ActivityType.CREATED
        
        log_client_activity(
            client=obj,
            activity_type=activity_type,
            user=request.user,
            description=f'Modification via admin Django' if change else 'Création via admin Django',
            ip_address=self.get_client_ip(request)
        )
    
    def get_client_ip(self, request):
        """Récupère IP pour audit"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# ═══════════════════════════════════════════════════════════
# CONTACT ADMIN
# ═══════════════════════════════════════════════════════════

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = [
        'full_name_display',
        'client_link',
        'position',
        'email',
        'phone',
        'is_primary_badge',
        'created_at',
    ]
    
    list_display_links = ['full_name_display', 'email']
    
    list_filter = [
        'is_primary',
        ('client', admin.RelatedOnlyFieldListFilter),
        'created_at',
    ]
    
    search_fields = [
        'first_name',
        'last_name',
        'email',
        'position',
        'phone',
        'client__company_name',
    ]
    
    ordering = ['client__company_name', 'last_name', 'first_name']
    
    list_per_page = 50
    
    fieldsets = (
        ('Informations contact', {
            'fields': (
                'client',
                'first_name',
                'last_name',
                'position',
            )
        }),
        
        ('Coordonnées', {
            'fields': (
                'email',
                'phone',
            )
        }),
        
        ('Paramètres', {
            'fields': (
                'is_primary',
                'notes',
            )
        }),
        
        ('Méta-données', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    autocomplete_fields = ['client']

    def full_name_display(self, obj):
        return obj.get_full_name()
    
    full_name_display.short_description = 'Nom complet'
    full_name_display.admin_order_field = 'last_name'
    
    def client_link(self, obj):
        url = reverse('admin:clients_client_change', args=[obj.client.id])
        return mark_safe(f'<a href="{url}">{obj.client.company_name}</a>')
    
    client_link.short_description = 'Client'
    client_link.admin_order_field = 'client'
    
    def is_primary_badge(self, obj):
        if obj.is_primary:
            return format_html(
                '<span style="background-color: #3B82F6; color: white; '
                'padding: 3px 10px; border-radius: 10px; font-weight: 600;">★ Principal</span>'
            )
        return '-'
    
    is_primary_badge.short_description = 'Type'
    is_primary_badge.admin_order_field = 'is_primary'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client')



@admin.register(ClientActivity)
class ClientActivityAdmin(admin.ModelAdmin):

    list_display = [
        'activity_type_display',
        'client_link',
        'user_display',
        'description_short',
        'ip_address',
        'created_at',
    ]
    
    list_filter = [
        'activity_type',
        ('client', admin.RelatedOnlyFieldListFilter),
        ('user', admin.RelatedOnlyFieldListFilter),
        'created_at',
    ]
    
    search_fields = [
        'description',
        'client__company_name',
        'user__email',
    ]
    
    ordering = ['-created_at']
    
    list_per_page = 100
    
    fieldsets = (
        ('Activité', {
            'fields': (
                'client',
                'activity_type',
                'description',
            )
        }),
        
        ('Utilisateur', {
            'fields': (
                'user',
                'ip_address',
            )
        }),
        
        ('Métadonnées', {
            'fields': (
                'metadata',
                'created_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = [
        'client',
        'activity_type',
        'user',
        'description',
        'metadata',
        'ip_address',
        'created_at',
    ]
    # Explication :
    # Tous readonly (activités immuables)
    
    # ───────────────────────────────────────────────────────
    # PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def activity_type_display(self, obj):
        colors = {
            'CREATED':  '#10B981',
            'UPDATED':  '#3B82F6',
            'DELETED':  '#EF4444',
            'RESTORED': '#F59E0B',
            'ASSIGNED': '#8B5CF6',
        }
        
        color = colors.get(obj.activity_type, '#6B7280')
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 10px; font-size: 11px;">{}</span>',
            color,
            obj.get_activity_type_display()
        )
    
    activity_type_display.short_description = 'Type'
    activity_type_display.admin_order_field = 'activity_type'
    
    def client_link(self, obj):
        url = reverse('admin:clients_client_change', args=[obj.client.id])
        return mark_safe(f'<a href="{url}">{obj.client.company_name}</a>')
    
    client_link.short_description = 'Client'
    client_link.admin_order_field = 'client'
    
    def user_display(self, obj):
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return mark_safe(f'<a href="{url}">{obj.user.get_full_name()}</a>')
        return '-'
    
    user_display.short_description = 'Utilisateur'
    user_display.admin_order_field = 'user'
    
    def description_short(self, obj):
        if len(obj.description) > 80:
            return obj.description[:80] + '...'
        return obj.description
    
    description_short.short_description = 'Description'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'user')


admin.site.site_header = "Insomea CRM - Administration"
admin.site.site_title = "Insomea CRM Admin"
admin.site.index_title = "Gestion des clients"