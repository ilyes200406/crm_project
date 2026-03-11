from django.conf import settings
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    SetupAccountSerializer,
)
from ..emails import send_password_reset_email
from ..models.passwordResetToken import PasswordResetToken
from ...users.api.serializers import UserSerializer


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def revoke_all_refresh_tokens_for_user(user):
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    for outstanding_token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=outstanding_token)


class SetupAccountView(generics.GenericAPIView):
    serializer_class = SetupAccountSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        tokens = get_tokens_for_user(user)

        return Response({
            'message': 'Compte configure avec succes. Vous pouvez maintenant vous connecter.',
            'user': UserSerializer(user).data,
            'tokens': tokens,
        }, status=status.HTTP_200_OK)


@method_decorator(ratelimit(key='ip', rate='5/15m', method='POST', block=True), name='post')
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)

        from django.utils import timezone
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return Response({
            'message': 'Connexion reussie.',
            'user': UserSerializer(user).data,
            'tokens': tokens,
        }, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]  

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')

            if not refresh_token:
                return Response(
                    {'error': 'Refresh token requis.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                'message': 'Deconnexion reussie.'
            }, status=status.HTTP_200_OK)

        except Exception:
            return Response(
                {'error': 'Token invalide ou deja blackliste.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        revoke_all_refresh_tokens_for_user(user)

        return Response({
            'message': 'Mot de passe change avec succes. Veuillez vous reconnecter sur tous vos appareils.'
        }, status=status.HTTP_200_OK)


@method_decorator(ratelimit(key='ip', rate='3/15m', method='POST', block=True), name='post')
class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        if user:
            ip_address = self.get_client_ip(request)
            reset_token = PasswordResetToken.generate_for_user(user, ip_address)
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token.token}"
            send_password_reset_email(user, reset_url)

        return Response({
            'message': 'Si cet email existe dans notre systeme, vous recevrez un lien de reinitialisation.'
        }, status=status.HTTP_200_OK)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        revoke_all_refresh_tokens_for_user(user)

        return Response({
            'message': 'Mot de passe reinitialise avec succes. Vous pouvez maintenant vous connecter.'
        }, status=status.HTTP_200_OK)
