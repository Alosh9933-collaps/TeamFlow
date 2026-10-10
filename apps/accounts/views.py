from django.shortcuts import render
from django.conf import settings
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.models import User
from django.core import signing
from django.utils.http import urlsafe_base64_decode

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
    inline_serializer,
)

from apps.accounts.serializers import RegisterSerializer, ChangePasswordSerializer, UserSerializer

from apps.accounts.services import (
    activate_user_from_verification,
    verify_email_verification_token,
    generate_email_verification_token,
    send_verification_email,
    resend_verification_email,
    generate_password_reset_token,
    generate_password_reset_uid,
    reset_user_password,
    send_password_reset_email,
    is_valid_password_reset_token,
    change_user_password,
    blacklist_refresh_token,
    )
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from django.contrib.auth import get_user_model

from django.contrib.auth.password_validation import validate_password

from rest_framework_simplejwt.exceptions import TokenError

class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: {
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "string",
                    },
                    "user_id": {
                        "type": "integer",
                    },
                    "email": {
                        "type": "string",
                        "format": "email",
                    },
                },
            },
            400: {
                "type": "object",
            },
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.save()

        token = generate_email_verification_token(
            user
        )

        uidb64 = urlsafe_base64_encode(
            force_bytes(user.id)
        )

        verification_path = reverse(
            "verify-email",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        verification_url = request.build_absolute_uri(
            verification_path
        )

        send_verification_email(
            user,
            verification_url,
        )

        return Response(
            {
                "detail": (
                    "Registration successful. "
                    "Please verify your email."
                ),
                "user_id": user.id,
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(
                name="uidb64",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
            ),
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
        },
    )

    def get(self, request, uidb64, token):
        try:
            user_id = urlsafe_base64_decode(
                uidb64
            ).decode()

            user = User.objects.get(
                id=user_id
            )

            token_user_id = verify_email_verification_token(
                token
            )

            if token_user_id != str(user.id):
                raise ValueError(
                    "Invalid verification token."
                )

            activate_user_from_verification(user)

        except (
            User.DoesNotExist,
            ValueError,
            signing.BadSignature,
            signing.SignatureExpired,
        ):
            return Response(
                {
                    "detail": (
                        "Invalid or expired "
                        "verification link."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": (
                    "Email verified successfully."
                )
            },
            status=status.HTTP_200_OK,
        )

class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={
            200: OpenApiTypes.OBJECT,
        },
    )

    def post(self, request):
        email = request.data.get("email", "")

        if not email:
            return Response(
                {
                    "detail": (
                        "If an account exists for this email, "
                        "a verification email will be sent."
                    )
                },
                status=status.HTTP_200_OK,
            )

        user = User.objects.filter(
            email__iexact=email
        ).first()

        if user and not user.is_active:
            token = generate_email_verification_token(
                user
            )

            uidb64 = urlsafe_base64_encode(
                force_bytes(user.id)
            )

            verification_path = reverse(
                "verify-email",
                kwargs={
                    "uidb64": uidb64,
                    "token": token,
                },
            )

            verification_url = (
                request.build_absolute_uri(
                    verification_path
                )
            )

            resend_verification_email(
                user,
                verification_url,
            )

        return Response(
            {
                "detail": (
                    "If an account exists for this email, "
                    "a verification email will be sent."
                )
            },
            status=status.HTTP_200_OK,
        )

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=inline_serializer(
            name="PasswordResetRequestRequest",
            fields={
                "email": serializers.EmailField(),
            },
        ),
        responses={
            200: inline_serializer(
                name="PasswordResetRequestResponse",
                fields={
                    "detail": serializers.CharField(),
                },
            ),
        },
    )

    def post(self, request):
        email = request.data.get("email", "").strip()

        user = User.objects.filter(
            email__iexact=email,
            is_active=True,
        ).first()

        if user:
            token = generate_password_reset_token(
                user
            )

            uidb64 = generate_password_reset_uid(
                user
            )

            # The email must link to the React page, not the API endpoint.
            # Set FRONTEND_URL in Django settings for each environment.
            frontend_url = getattr(
                settings,
                "FRONTEND_URL",
                "http://127.0.0.1:5173",
            ).rstrip("/")
            reset_url = (
                f"{frontend_url}/reset-password/"
                f"{uidb64}/{token}"
            )

            send_password_reset_email(
                user,
                reset_url,
            )

        return Response(
            {
                "detail": (
                    "If an account exists for this email, "
                    "a password reset email will be sent."
                )
            },
            status=status.HTTP_200_OK,
        )

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="auth_password_reset_confirm",
        request=OpenApiTypes.OBJECT,
        parameters=[
            OpenApiParameter(
                name="uidb64",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
            ),
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
        },
    )

    def post(self, request, uidb64, token):
        password = request.data.get(
            "password",
            "",
        )

        password_confirm = request.data.get(
            "password_confirm",
            "",
        )

        if password != password_confirm:
            return Response(
                {
                    "password_confirm": (
                        "Passwords do not match."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = urlsafe_base64_decode(
                uidb64
            ).decode()

            user = User.objects.get(
                id=user_id,
                is_active=True,
            )

        except (
            User.DoesNotExist,
            ValueError,
            TypeError,
            OverflowError,
        ):
            return Response(
                {
                    "detail": (
                        "Invalid or expired "
                        "password reset link."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not is_valid_password_reset_token(
            user,
            token,
        ):
            return Response(
                {
                    "detail": (
                        "Invalid or expired "
                        "password reset link."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(
                password,
                user,
            )
        except Exception as exc:
            return Response(
                {
                    "password": list(
                        getattr(
                            exc,
                            "messages",
                            [
                                "Invalid password."
                            ],
                        )
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_user_password(
            user,
            password,
        )

        return Response(
            {
                "detail": (
                    "Password reset successfully."
                )
            },
            status=status.HTTP_200_OK,
        )

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={
            200: inline_serializer(
                name="ChangePasswordResponse",
                fields={
                    "detail": serializers.CharField(),
                },
            ),
            400: inline_serializer(
                name="ChangePasswordErrorResponse",
                fields={
                    "detail": serializers.CharField(),
                },
            ),
        },
    )

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            change_user_password(
                user=request.user,
                old_password=(
                    serializer.validated_data[
                        "old_password"
                    ]
                ),
                new_password=(
                    serializer.validated_data[
                        "new_password"
                    ]
                ),
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": (
                    "Password changed successfully."
                )
            },
            status=status.HTTP_200_OK,
        )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={
            200: inline_serializer(
                name="LogoutResponse",
                fields={
                    "detail": serializers.CharField(),
                },
            ),
        },
    )

    def post(self, request):
        refresh_token = request.data.get(
            "refresh"
        )

        if not refresh_token:
            return Response(
                {
                    "detail": (
                        "Refresh token is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            blacklist_refresh_token(
                refresh_token
            )
        except TokenError:
            return Response(
                {
                    "detail": (
                        "Invalid or expired "
                        "refresh token."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Logged out successfully."
            },
            status=status.HTTP_200_OK,
        )

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={
            200: UserSerializer,
        },
    )

    def get(self, request):
        serializer = UserSerializer(
            request.user
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
