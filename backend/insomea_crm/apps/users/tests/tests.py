from django.test import RequestFactory, TestCase

from ..api.serializers import AdminCreateUserSerializer, UserUpdateSerializer
from ..models.users import RoleChoices, Utilisateur


class UserSerializerTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_admin_create_user_email_uniqueness_is_case_insensitive(self):
        Utilisateur.objects.create_user(
            email='test@example.com',
            role=RoleChoices.COMMERCIAL,
        )

        serializer = AdminCreateUserSerializer(data={
            'email': 'TEST@EXAMPLE.COM',
            'role': RoleChoices.TECHNICIEN,
            'first_name': 'Test',
            'last_name': 'User',
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_user_update_email_uniqueness_is_case_insensitive(self):
        owner = Utilisateur.objects.create_user(
            email='owner@example.com',
            role=RoleChoices.COMMERCIAL,
            is_active=True,
            is_verified=True,
        )
        Utilisateur.objects.create_user(
            email='other@example.com',
            role=RoleChoices.COMMERCIAL,
            is_active=True,
            is_verified=True,
        )

        request = self.factory.put('/api/auth/me/')
        request.user = owner

        serializer = UserUpdateSerializer(
            owner,
            data={'email': 'OTHER@EXAMPLE.COM'},
            context={'request': request},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
