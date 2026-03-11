from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from ...users.models.users import User
from ..models.setupToken import SetupToken
from ..models.passwordResetToken import PasswordResetToken 


class SetupAccountSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=True,
        help_text="Token recu par email"
    )

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Nouveau mot de passe (min 8 caracteres)"
    )

    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Confirmation du mot de passe"
    )

    first_name = serializers.CharField(
        required=False,
        allow_blank=True
    )

    last_name = serializers.CharField(
        required=False,
        allow_blank=True
    )

    def validate_token(self, value):
        try:
            setup_token = SetupToken.objects.select_related('user').get(token=value)
        except SetupToken.DoesNotExist:
            raise serializers.ValidationError(
                "Token invalide ou expire."
            )

        if not setup_token.is_valid():
            if setup_token.is_used:
                raise serializers.ValidationError(
                    "Ce token a deja ete utilise."
                )
            raise serializers.ValidationError(
                "Ce token a expire. Contactez l'administrateur."
            )

        self.context['setup_token'] = setup_token
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))

        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Les mots de passe ne correspondent pas."
            })

        return attrs

    def save(self):
        with transaction.atomic():
            setup_token = SetupToken.objects.select_for_update().select_related('user').get(
                pk=self.context['setup_token'].pk
            )

            if not setup_token.is_valid():
                raise serializers.ValidationError({'token': "Token invalide ou expire."})

            user = setup_token.user
            user.set_password(self.validated_data['password'])

            if self.validated_data.get('first_name'):
                user.first_name = self.validated_data['first_name']
            if self.validated_data.get('last_name'):
                user.last_name = self.validated_data['last_name']

            user.is_active = True
            user.is_verified = True
            user.save()

            setup_token.mark_as_used()
            return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        if not user:
            raise serializers.ValidationError(
                "Email ou mot de passe incorrect.",
                code='authorization'
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "Ce compte n'est pas encore active. Verifiez votre email.",
                code='authorization'
            )
        """
        if not user.is_verified:
            raise serializers.ValidationError(
                "Votre adresse email n'est pas verifiee.",
                code='authorization'
            )
        """
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        user = self.context['request'].user

        if not user.check_password(value):
            raise serializers.ValidationError(
                "Mot de passe actuel incorrect."
            )

        return value

    def validate_new_password(self, value):
        user = self.context['request'].user

        try:
            validate_password(value, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))

        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': "Les mots de passe ne correspondent pas."
            })

        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()

        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        return value.lower()

    def save(self):
        email = self.validated_data['email']

        try:
            user = User.objects.get(email__iexact=email, is_active=True)
            return user
        except User.DoesNotExist:
            return None


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)

    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate_token(self, value):
        try:
            reset_token = PasswordResetToken.objects.select_related('user').get(token=value)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError(
                "Token invalide ou expire."
            )

        if not reset_token.is_valid():
            if reset_token.is_used:
                raise serializers.ValidationError(
                    "Ce token a deja ete utilise."
                )
            raise serializers.ValidationError(
                "Ce token a expire. Veuillez demander un nouveau lien."
            )

        self.context['reset_token'] = reset_token
        return value

    def validate_new_password(self, value):
        user = self.context.get('reset_token').user if 'reset_token' in self.context else None

        try:
            validate_password(value, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))

        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': "Les mots de passe ne correspondent pas."
            })

        return attrs

    def save(self):
        with transaction.atomic():
            reset_token = PasswordResetToken.objects.select_for_update().select_related('user').get(
                pk=self.context['reset_token'].pk
            )

            if not reset_token.is_valid():
                raise serializers.ValidationError({'token': "Token invalide ou expire."})

            user = reset_token.user
            user.set_password(self.validated_data['new_password'])
            user.save()

            reset_token.mark_as_used()
            return user