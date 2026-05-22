from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .models import DemandeClient, StatutDemande
from .permissions import IsCommercialOrAdmin, IsAssignedCommercialOrAdmin
from .serializers import (
    ConvertirDemandeSerializer,
    DemandeClientDetailSerializer,
    DemandeClientListSerializer,
    PublicDemandeSerializer,
)


class DemandeSubmitThrottle(AnonRateThrottle):
    rate = '10/hour'


# ═══════════════════════════════════════════════════════════
# PUBLIC — soumission sans authentification
# ═══════════════════════════════════════════════════════════

class PublicDemandeCreateView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [DemandeSubmitThrottle]

    def post(self, request):
        serializer = PublicDemandeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        demande = serializer.save()

        # Notifier commerciaux + admins (best-effort)
        try:
            from .notifications import notify_nouveau_lead
            notify_nouveau_lead(demande)
        except Exception:
            pass

        return Response(
            {"message": "Votre demande a bien été reçue. Notre équipe vous contactera prochainement."},
            status=status.HTTP_201_CREATED,
        )


# ═══════════════════════════════════════════════════════════
# INTERNE — gestion des demandes (commerciaux + admins)
# ═══════════════════════════════════════════════════════════

class DemandeClientViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsCommercialOrAdmin]

    def get_queryset(self):
        user = self.request.user

        if user.role_id == 'ADMIN':
            return DemandeClient.objects.select_related('prise_en_charge_par', 'opportunite').all()

        # Commercial : voit NOUVELLE (toutes) + ses propres PRISE_EN_CHARGE
        from django.db.models import Q
        return DemandeClient.objects.select_related(
            'prise_en_charge_par', 'opportunite'
        ).filter(
            Q(statut=StatutDemande.NOUVELLE) |
            Q(statut=StatutDemande.PRISE_EN_CHARGE, prise_en_charge_par=user)
        )

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DemandeClientDetailSerializer
        return DemandeClientListSerializer

    @action(detail=True, methods=['post'], url_path='prendre-en-charge')
    def prendre_en_charge(self, request, pk=None):
        demande = self.get_object()

        if demande.statut != StatutDemande.NOUVELLE:
            return Response(
                {"detail": "Cette demande a déjà été prise en charge ou n'est plus disponible."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        demande.statut = StatutDemande.PRISE_EN_CHARGE
        demande.prise_en_charge_par = request.user
        demande.prise_en_charge_at = timezone.now()
        demande.save(update_fields=['statut', 'prise_en_charge_par', 'prise_en_charge_at'])

        return Response(DemandeClientDetailSerializer(demande).data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, IsCommercialOrAdmin, IsAssignedCommercialOrAdmin],
    )
    def convertir(self, request, pk=None):
        demande = self.get_object()

        if demande.statut not in (StatutDemande.NOUVELLE, StatutDemande.PRISE_EN_CHARGE):
            return Response(
                {"detail": "Seules les demandes nouvelles ou en cours peuvent être converties."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ConvertirDemandeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        opportunite_id = serializer.validated_data.get('opportunite_id')

        if opportunite_id:
            from apps.ventes.models import Opportunity
            try:
                opp = Opportunity.objects.get(id=opportunite_id)
            except Opportunity.DoesNotExist:
                return Response({"detail": "Opportunité introuvable."}, status=status.HTTP_404_NOT_FOUND)
            demande.opportunite = opp

        demande.statut = StatutDemande.CONVERTIE
        demande.save(update_fields=['statut', 'opportunite'])

        return Response(DemandeClientDetailSerializer(demande).data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, IsCommercialOrAdmin, IsAssignedCommercialOrAdmin],
    )
    def annuler(self, request, pk=None):
        demande = self.get_object()

        if demande.statut in (StatutDemande.CONVERTIE, StatutDemande.ANNULEE):
            return Response(
                {"detail": "Cette demande ne peut pas être annulée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        demande.statut = StatutDemande.ANNULEE
        demande.save(update_fields=['statut'])

        return Response(DemandeClientDetailSerializer(demande).data)
