from django.test import TestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from ..api.serializers import LoginSerializer, SetupAccountSerializer
from ..models.setupToken import SetupToken
from ..api.views import revoke_all_refresh_tokens_for_user
from ...users.models.users import RoleChoices, User


class AuthenticationFlowTests(TestCase):
    def test_setup_account_marks_user_verified(self):
        user = User.objects.create_user(
            email='new.user@example.com',
            role=RoleChoices.COMMERCIAL,
            is_active=False,
            is_verified=False,
        )
        setup_token = SetupToken.generate_for_user(user)

        serializer = SetupAccountSerializer(data={
            'token': setup_token.token,
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'first_name': 'New',
            'last_name': 'User',
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()

        updated_user.refresh_from_db()
        setup_token.refresh_from_db()

        self.assertTrue(updated_user.is_active)
        self.assertTrue(updated_user.is_verified)
        self.assertTrue(setup_token.is_used)

    def test_login_rejects_unverified_user(self):
        user = User.objects.create_user(
            email='pending@example.com',
            password='StrongPass123!',
            role=RoleChoices.COMMERCIAL,
            is_active=True,
            is_verified=False,
        )

        serializer = LoginSerializer(data={
            'email': user.email,
            'password': 'StrongPass123!',
        }, context={'request': None})

        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_revoke_all_refresh_tokens_blacklists_existing_tokens(self):
        user = User.objects.create_user(
            email='session.user@example.com',
            password='StrongPass123!',
            role=RoleChoices.COMMERCIAL,
            is_active=True,
            is_verified=True,
        )

        RefreshToken.for_user(user)
        RefreshToken.for_user(user)

        self.assertGreater(OutstandingToken.objects.filter(user=user).count(), 0)

        revoke_all_refresh_tokens_for_user(user)

        outstanding = OutstandingToken.objects.filter(user=user)
        blacklisted_count = BlacklistedToken.objects.filter(token__in=outstanding).count()

        self.assertEqual(blacklisted_count, outstanding.count())
