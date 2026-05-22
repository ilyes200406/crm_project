from rest_framework import serializers
from .models import DemandeClient


class PublicDemandeSerializer(serializers.ModelSerializer):
    """Serializer pour la soumission publique (sans auth)."""

    class Meta:
        model = DemandeClient
        fields = ('nom_entreprise', 'nom_contact', 'email', 'telephone', 'message', 'produits_suggeres')

    def validate_message(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Le message doit contenir au moins 10 caractères.")
        return value.strip()

    def validate_nom_entreprise(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Le nom de l'entreprise doit contenir au moins 2 caractères.")
        return value.strip()

    def validate_nom_contact(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Le nom du contact doit contenir au moins 2 caractères.")
        return value.strip()


class DemandeClientListSerializer(serializers.ModelSerializer):
    prise_en_charge_par_nom = serializers.CharField(
        source='prise_en_charge_par.get_full_name',
        read_only=True,
        default=None,
    )

    class Meta:
        model = DemandeClient
        fields = (
            'id', 'nom_entreprise', 'nom_contact', 'email', 'telephone',
            'statut', 'prise_en_charge_par_nom', 'created_at',
        )


class DemandeClientDetailSerializer(serializers.ModelSerializer):
    prise_en_charge_par_nom = serializers.CharField(
        source='prise_en_charge_par.get_full_name',
        read_only=True,
        default=None,
    )
    opportunite_reference = serializers.CharField(
        source='opportunite.reference',
        read_only=True,
        default=None,
    )

    class Meta:
        model = DemandeClient
        fields = (
            'id', 'nom_entreprise', 'nom_contact', 'email', 'telephone',
            'message', 'produits_suggeres', 'statut',
            'prise_en_charge_par_nom', 'prise_en_charge_at',
            'opportunite_reference', 'created_at',
        )


class ConvertirDemandeSerializer(serializers.Serializer):
    opportunite_id = serializers.UUIDField(required=False, allow_null=True)
