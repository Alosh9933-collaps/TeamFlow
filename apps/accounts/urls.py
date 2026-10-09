from django.urls import path
from apps.accounts.views import (
    RegisterView,
    VerifyEmailView,
)

from django.urls import path

from apps.accounts.views import (
    RegisterView,
    VerifyEmailView,
    ResendVerificationEmailView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ChangePasswordView,
    LogoutView,
    MeView,
)


urlpatterns = [
    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),
    path(
        "verify-email/<uidb64>/<token>/",
        VerifyEmailView.as_view(),
        name="verify-email",
    ),
    path(
        "resend-verification/",
        ResendVerificationEmailView.as_view(),
        name="resend-verification",
    ),
    path(
        "password-reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
        path(
        "me/",
        MeView.as_view(),
        name="me",
    ),
]
