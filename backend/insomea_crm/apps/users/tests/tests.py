from django.test import RequestFactory, TestCase

from ..api.serializers import AdminCreateUserSerializer, UserUpdateSerializer
from ..models.users import User as Utilisateur
from ..models.role import Role


class UserSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.get_or_create(name='COMMERCIAL', defaults={'display_name': 'Commercial'})
        Role.objects.get_or_create(name='TECHNICIEN', defaults={'display_name': 'Technicien'})

    def setUp(self):
        self.factory = RequestFactory()

    def test_admin_create_user_email_uniqueness_is_case_insensitive(self):
        Utilisateur.objects.create_user(
            email='test@example.com',
            role_id='COMMERCIAL',
        )

        serializer = AdminCreateUserSerializer(data={
            'email': 'TEST@EXAMPLE.COM',
            'role': 'TECHNICIEN',
            'first_name': 'Test',
            'last_name': 'User',
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_user_update_email_uniqueness_is_case_insensitive(self):
        owner = Utilisateur.objects.create_user(
            email='owner@example.com',
            role_id='COMMERCIAL',
            is_active=True,
            is_verified=True,
        )
        Utilisateur.objects.create_user(
            email='other@example.com',
            role_id='COMMERCIAL',
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
