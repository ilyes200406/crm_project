from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.utils.html import format_html

from ..authentication.emails import send_setup_email
from ..authentication.models.setupToken import SetupToken
from .models.permission import Permission, RolePermission
from .models.users import User


# ---------------------------------------------------------------------------
# Custom Forms
# ---------------------------------------------------------------------------

class UserAddForm(forms.ModelForm):
    """Form used only on the Add User page — no password fields."""

    class Meta:
        model = User
        fields = ('email', 'role', 'first_name', 'last_name')

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un utilisateur avec cet email existe déjà.")
        return email


class UserChangeForm(forms.ModelForm):
    """Form used on the Edit User page — no password, no is_verified."""

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')


# ---------------------------------------------------------------------------
# UserAdmin
# ---------------------------------------------------------------------------

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    add_form = UserAddForm
    form = UserChangeForm

    # --- List view ---
    list_display = (
        'email',
        'full_name_display',
        'role_badge',
        'status_badge',
        'is_verified',
        'date_joined',
        'last_login',
    )
    list_filter = ('role', 'is_active', 'is_verified', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    # --- Edit page ---
    readonly_fields = (
        'id',
        'date_joined',
        'last_login',
        'created_at',
        'updated_at',
        'is_verified',
        'setup_token_info',
    )

    fieldsets = (
        ('Identité', {
            'fields': ('email', 'first_name', 'last_name'),
        }),
        ('Rôle & Statut', {
            'fields': ('role', 'is_active', 'is_staff'),
        }),
        ('Vérification', {
            'fields': ('is_verified', 'setup_token_info'),
        }),
        ('Métadonnées', {
            'fields': ('id', 'date_joined', 'last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # --- Add page ---
    add_fieldsets = (
        ('Nouvel utilisateur', {
            'fields': ('email', 'role', 'first_name', 'last_name'),
            'description': (
                "Un email d'invitation avec un lien de configuration "
                "sera automatiquement envoyé à l'utilisateur."
            ),
        }),
    )

    # --- Actions ---
    actions = ['resend_invitation', 'activate_users', 'deactivate_users']

    # -----------------------------------------------------------------------
    # Form / fieldset switching (add vs. change)
    # -----------------------------------------------------------------------

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs['form'] = self.add_form
        else:
            kwargs['form'] = self.form
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    # -----------------------------------------------------------------------
    # Save logic — triggers invitation email on creation
    # -----------------------------------------------------------------------

    def save_model(self, request, obj, form, change):
        if not change:
            # CREATE PATH: use UserManager so password and flags are set correctly
            user = User.objects.create_user(
                email=form.cleaned_data['email'],
                password=None,
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', ''),
                role=form.cleaned_data['role'],
            )
            # Populate obj.pk so Django admin can redirect to the change page
            obj.pk = user.pk

            setup_token = SetupToken.generate_for_user(user)
            setup_url = f"{settings.FRONTEND_URL}/setup?token={setup_token.token}"

            try:
                send_setup_email(user, setup_url)
                self.message_user(
                    request,
                    f"Utilisateur {user.email} créé. Email d'invitation envoyé.",
                    messages.SUCCESS,
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"Utilisateur créé mais l'envoi d'email a échoué : {e}",
                    messages.WARNING,
                )
            # Do NOT call super() — user is already persisted by create_user()
        else:
            super().save_model(request, obj, form, change)

    # -----------------------------------------------------------------------
    # Custom display methods
    # -----------------------------------------------------------------------

    def full_name_display(self, obj):
        return obj.get_full_name()
    full_name_display.short_description = 'Nom complet'

    def role_badge(self, obj):
        colors = {
            'ADMIN':      '#9C27B0',
            'COMMERCIAL': '#2196F3',
            'TECHNICIEN': '#FF9800',
            'FINANCE':    '#4CAF50',
        }
        color = colors.get(obj.role, '#9E9E9E')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:3px;">{}</span>',
            color,
            obj.get_role_display(),
        )
    role_badge.short_description = 'Rôle'

    def status_badge(self, obj):
        if obj.is_active and obj.is_verified:
            color, label = '#4CAF50', 'Actif'
        elif not obj.is_active and not obj.is_verified:
            color, label = '#FF9800', 'En attente'
        elif obj.is_active and not obj.is_verified:
            color, label = '#2196F3', 'Non vérifié'
        else:
            color, label = '#F44336', 'Inactif'
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:3px;">{}</span>',
            color, label,
        )
    status_badge.short_description = 'Statut'

    def setup_token_info(self, obj):
        try:
            token = obj.setup_token
            if token.is_used:
                return format_html('<span style="color:green;">Token utilisé (compte configuré)</span>')
            elif not token.is_valid():
                return format_html('<span style="color:red;">Token expiré</span>')
            else:
                return format_html(
                    '<span style="color:orange;">Token actif — expire le {}</span>',
                    token.expires_at.strftime('%d/%m/%Y %H:%M'),
                )
        except SetupToken.DoesNotExist:
            return format_html('<span style="color:gray;">Aucun token actif</span>')
    setup_token_info.short_description = "Token d'invitation"

    # -----------------------------------------------------------------------
    # Custom actions
    # -----------------------------------------------------------------------

    @admin.action(description="Renvoyer l'email d'invitation")
    def resend_invitation(self, request, queryset):
        sent = skipped = 0
        for user in queryset:
            if user.is_active:
                skipped += 1
                continue
            setup_token = SetupToken.generate_for_user(user)
            setup_url = f"{settings.FRONTEND_URL}/setup?token={setup_token.token}"
            try:
                send_setup_email(user, setup_url)
                sent += 1
            except Exception as e:
                self.message_user(request, f"Echec d'envoi pour {user.email} : {e}", messages.WARNING)
        if sent:
            self.message_user(request, f"{sent} invitation(s) renvoyée(s).", messages.SUCCESS)
        if skipped:
            self.message_user(request, f"{skipped} utilisateur(s) déjà actif(s) ignoré(s).", messages.WARNING)

    @admin.action(description='Activer les utilisateurs sélectionnés')
    def activate_users(self, request, queryset):
        count = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, f"{count} utilisateur(s) activé(s).", messages.SUCCESS)

    @admin.action(description='Désactiver les utilisateurs sélectionnés')
    def deactivate_users(self, request, queryset):
        count = queryset.exclude(pk=request.user.pk).filter(is_active=True).update(is_active=False)
        self.message_user(request, f"{count} utilisateur(s) désactivé(s).", messages.SUCCESS)


# ---------------------------------------------------------------------------
# Permission & RolePermission admins
# ---------------------------------------------------------------------------

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'name', 'created_at')
    search_fields = ('codename', 'name')
    readonly_fields = ('created_at',)
    ordering = ('codename',)


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission_codename', 'permission_name')
    list_filter = ('role',)
    search_fields = ('permission__codename', 'permission__name')
    autocomplete_fields = ('permission',)

    def permission_codename(self, obj):
        return obj.permission.codename
    permission_codename.short_description = 'Codename'
    permission_codename.admin_order_field = 'permission__codename'

    def permission_name(self, obj):
        return obj.permission.name
    permission_name.short_description = 'Nom permission'
