from django.contrib import admin
from .models import DemandeClient


@admin.register(DemandeClient)
class DemandeClientAdmin(admin.ModelAdmin):
    list_display = ('nom_entreprise', 'nom_contact', 'email', 'statut', 'prise_en_charge_par', 'created_at')
    list_filter = ('statut', 'created_at')
    search_fields = ('nom_entreprise', 'nom_contact', 'email')
    readonly_fields = ('id', 'created_at', 'prise_en_charge_at')
    ordering = ('-created_at',)
