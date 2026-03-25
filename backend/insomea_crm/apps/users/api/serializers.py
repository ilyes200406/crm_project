from rest_framework import serializers

from ..models.users import User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'is_active',
            'is_verified',
            'date_joined',
            'last_login',
        ]
        read_only_fields = [
            'id',
            'date_joined',
            'last_login',
            'is_verified',
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserMinimalSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()


class AdminCreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'email',
            'role',
            'first_name',
            'last_name',
        ]

    def validate_email(self, value):
        normalized = value.lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError(
                "Un utilisateur avec cet email existe deja."
            )
        return normalized

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            password=None,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data['role'],
            is_active=False,
            is_verified=False,
        )


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
        ]

    def validate_email(self, value):
        user = self.context['request'].user
        normalized = value.lower()

        if normalized != user.email.lower():
            if User.objects.filter(email__iexact=normalized).exists():
                raise serializers.ValidationError(
                    "Cet email est deja utilise."
                )

        return normalized

    def update(self, instance, validated_data):
        email_changed = 'email' in validated_data and validated_data['email'].lower() != instance.email.lower()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if email_changed:
            instance.is_verified = False

        instance.save()
        return instance
