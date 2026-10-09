from django.test import TestCase
from django.core import mail
from rest_framework.test import APIClient
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.accounts.services import (
    generate_email_verification_token,
    generate_password_reset_token,
    generate_password_reset_uid,
)
from django.contrib.auth import get_user_model
User = get_user_model()

class JWTAuthenticationTests(TestCase):
    def setUp(self):
        from apps.accounts.models import User

        self.client = APIClient()

        self.user = User.objects.create_user(
            username="testuser",
            password="StrongPassword123!",
        )

    def test_user_can_login_and_receive_tokens(self):
        response = self.client.post(
            "/api/auth/token/",
            {
                "username": "testuser",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertIn(
            "refresh",
            response.data,
        )

    def test_login_fails_with_wrong_password(self):
        response = self.client.post(
            "/api/auth/token/",
            {
                "username": "testuser",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_refresh_token_returns_new_access_token(self):
        login_response = self.client.post(
            "/api/auth/token/",
            {
                "username": "testuser",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            "/api/auth/token/refresh/",
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "access",
            response.data,
        )

    from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIClient


User = get_user_model()


class RegisterTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_can_register(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        user = User.objects.get(
            username="newuser"
        )

        self.assertEqual(
            user.email,
            "newuser@example.com",
        )

        self.assertFalse(
            user.is_active,
        )

        self.assertTrue(
            user.check_password(
                "StrongPassword123!"
            )
        )

    def test_registration_rejects_weak_password(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "weakuser",
                "email": "weak@example.com",
                "password": "123",
                "password_confirm": "123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            User.objects.filter(
                username="weakuser"
            ).exists()
        )

    def test_registration_rejects_mismatched_passwords(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "mismatch",
                "email": "mismatch@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "DifferentPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            email="existing@example.com",
            password="StrongPassword123!",
        )

        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "anotheruser",
                "email": "EXISTING@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_unverified_user_cannot_login(self):
        register_response = self.client.post(
            "/api/auth/register/",
            {
                "username": "unverified",
                "email": "unverified@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            register_response.status_code,
            201,
        )

        login_response = self.client.post(
            "/api/auth/token/",
            {
                "username": "unverified",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            401,
        )

    def test_registration_sends_verification_email(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "emailuser",
                "email": "emailuser@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        self.assertIn(
            "Verify your TeamFlow account",
            mail.outbox[0].subject,
        )

        self.assertIn(
            "emailuser@example.com",
            mail.outbox[0].to,
        )

    def test_user_can_verify_email(self):
        user = User.objects.create_user(
            username="verifyuser",
            email="verify@example.com",
            password="StrongPassword123!",
            is_active=False,
        )

        token = generate_email_verification_token(
            user
        )

        uidb64 = urlsafe_base64_encode(
            force_bytes(user.id)
        )

        response = self.client.get(
            f"/api/auth/verify-email/"
            f"{uidb64}/{token}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        user.refresh_from_db()

        self.assertTrue(
            user.is_active,
        )

    def test_unverified_user_can_resend_verification_email(self):
        user = User.objects.create_user(
            username="resenduser",
            email="resend@example.com",
            password="StrongPassword123!",
            is_active=False,
        )

        response = self.client.post(
            "/api/auth/resend-verification/",
            {
                "email": "resend@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        self.assertIn(
            "resend@example.com",
            mail.outbox[0].to,
        )

    def test_verified_user_does_not_receive_verification_email(self):
        User.objects.create_user(
            username="verifieduser",
            email="verified@example.com",
            password="StrongPassword123!",
            is_active=True,
        )

        response = self.client.post(
            "/api/auth/resend-verification/",
            {
                "email": "verified@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(mail.outbox),
            0,
        )

    def test_resend_verification_does_not_reveal_unknown_email(self):
        response = self.client.post(
            "/api/auth/resend-verification/",
            {
                "email": "unknown@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(mail.outbox),
            0,
        )

        self.assertIn(
            "If an account exists",
            response.data["detail"],
        )
    def test_existing_active_user_can_request_password_reset(self):
        user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="OldPassword123!",
            is_active=True,
        )

        response = self.client.post(
            "/api/auth/password-reset/",
            {
                "email": "reset@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        self.assertIn(
            "reset@example.com",
            mail.outbox[0].to,
        )

    def test_unknown_email_does_not_reveal_account_existence(self):
        response = self.client.post(
            "/api/auth/password-reset/",
            {
                "email": "unknown@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(mail.outbox),
            0,
        )

    def test_user_can_reset_password(self):
        user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="OldPassword123!",
            is_active=True,
        )

        token = generate_password_reset_token(
            user
        )

        uidb64 = generate_password_reset_uid(
            user
        )

        response = self.client.post(
            f"/api/auth/password-reset/"
            f"{uidb64}/{token}/",
            {
                "password": "NewPassword123!",
                "password_confirm": "NewPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        user.refresh_from_db()

        self.assertTrue(
            user.check_password(
                "NewPassword123!"
            )
        )

    def test_password_reset_token_cannot_be_reused(self):
        user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="OldPassword123!",
            is_active=True,
        )

        token = generate_password_reset_token(
            user
        )

        uidb64 = generate_password_reset_uid(
            user
        )

        first_response = self.client.post(
            f"/api/auth/password-reset/"
            f"{uidb64}/{token}/",
            {
                "password": "NewPassword123!",
                "password_confirm": "NewPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            200,
        )

        second_response = self.client.post(
            f"/api/auth/password-reset/"
            f"{uidb64}/{token}/",
            {
                "password": "AnotherPassword123!",
                "password_confirm": "AnotherPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            400,
        )

    def test_authenticated_user_can_change_password(self):
        user = User.objects.create_user(
            username="changepass",
            email="change@example.com",
            password="OldPassword123!",
            is_active=True,
        )

        self.client.force_authenticate(
            user=user
        )

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "OldPassword123!",
                "new_password": "NewPassword123!",
                "new_password_confirm": (
                    "NewPassword123!"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        user.refresh_from_db()

        self.assertTrue(
            user.check_password(
                "NewPassword123!"
            )
        )

    def test_authenticated_user_can_change_password(self):
        user = User.objects.create_user(
            username="changepass",
            email="change@example.com",
            password="OldPassword123!",
            is_active=True,
        )

        self.client.force_authenticate(
            user=user
        )

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "OldPassword123!",
                "new_password": "NewPassword123!",
                "new_password_confirm": (
                    "NewPassword123!"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        user.refresh_from_db()

        self.assertTrue(
            user.check_password(
                "NewPassword123!"
            )
        )

    def test_user_can_logout_and_blacklist_refresh_token(self):
        user = User.objects.create_user(
            username="logoutuser",
            email="logout@example.com",
            password="StrongPassword123!",
            is_active=True,
        )

        login_response = self.client.post(
            "/api/auth/token/",
            {
                "username": "logoutuser",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            200,
        )

        refresh_token = login_response.data[
            "refresh"
        ]

        self.client.force_authenticate(
            user=user
        )

        logout_response = self.client.post(
            "/api/auth/logout/",
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            logout_response.status_code,
            200,
        )

        refresh_response = self.client.post(
            "/api/auth/token/refresh/",
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            refresh_response.status_code,
            401,
        )

    def test_logout_requires_refresh_token(self):
        user = User.objects.create_user(
            username="logoutmissing",
            email="logoutmissing@example.com",
            password="StrongPassword123!",
            is_active=True,
        )

        self.client.force_authenticate(
            user=user
        )

        response = self.client.post(
            "/api/auth/logout/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_refresh_token_is_rotated_and_old_token_is_blacklisted(self):
        user = User.objects.create_user(
            username="rotateuser",
            email="rotate@example.com",
            password="StrongPassword123!",
            is_active=True,
        )

        login_response = self.client.post(
            "/api/auth/token/",
            {
                "username": "rotateuser",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        old_refresh = login_response.data[
            "refresh"
        ]

        response = self.client.post(
            "/api/auth/token/refresh/",
            {
                "refresh": old_refresh,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        new_refresh = response.data[
            "refresh"
        ]

        self.assertNotEqual(
            old_refresh,
            new_refresh,
        )

        old_refresh_response = self.client.post(
            "/api/auth/token/refresh/",
            {
                "refresh": old_refresh,
            },
            format="json",
        )

        self.assertEqual(
            old_refresh_response.status_code,
            401,
        )

    def test_authenticated_user_can_access_me_endpoint(self):
        user = User.objects.create_user(
            username="meuser",
            email="me@example.com",
            password="StrongPassword123!",
            is_active=True,
        )

        login_response = self.client.post(
            "/api/auth/token/",
            {
                "username": user.username,
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            200,
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(
            "/api/auth/me/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            user.id,
        )

        self.assertEqual(
            response.data["username"],
            user.username,
        )

        self.assertEqual(
            response.data["email"],
            user.email,
        )

    def test_anonymous_user_cannot_access_me_endpoint(self):
        response = self.client.get(
            "/api/auth/me/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )
