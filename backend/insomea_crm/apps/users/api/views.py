from django.conf import settings
from django.db.models import Count, Q
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...authentication.emails import send_setup_email
from ..permissions import IsAdmin
from ...authentication.models.setupToken import SetupToken
from .serializers import AdminCreateUserSerializer, UserUpdateSerializer, UserSerializer
from ..models.users import User


class AdminCreateUserView(generics.CreateAPIView):
    serializer_class = AdminCreateUserSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        setup_token = SetupToken.generate_for_user(user)
        setup_url = f"{settings.FRONTEND_URL}/setup?token={setup_token.token}"
        send_setup_email(user, setup_url)

        return Response({
            'message': f'Utilisateur crée avec succés. Un email a été envoye à {user.email}.',
            'user': UserSerializer(user).data,
            'setup_token_expires_at': setup_token.expires_at,
        }, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        return Response(UserSerializer(user).data)


class UserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    filterset_fields = ['role', 'is_active', 'is_verified']
    search_fields = ['email', 'first_name', 'last_name']

    def get_queryset(self):
        queryset = super().get_queryset()

        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role_id=role)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        return queryset

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()

        if user == request.user:
            return Response(
                {'error': 'Vous ne pouvez pas vous desactiver vous-meme.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = False
        user.save(update_fields=['is_active'])

        return Response({
            'message': f'Utilisateur {user.email} desactive avec succes.'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()

        if user.is_active:
            return Response(
                {'message': 'Cet utilisateur est deja actif.'},
                status=status.HTTP_200_OK
            )

        user.is_active = True
        user.save(update_fields=['is_active'])

        return Response({
            'message': f'Utilisateur {user.email} active avec succes.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        total = User.objects.count()
        actifs = User.objects.filter(is_active=True).count()

        par_role = User.objects.values('role').annotate(count=Count('id'))

        return Response({
            'total': total,
            'actifs': actifs,
            'inactifs': total - actifs,
            'par_role': {item['role']: item['count'] for item in par_role},
        })
