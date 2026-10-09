from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.utils import timezone
from django.core.mail import send_mail

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from rest_framework_simplejwt.tokens import RefreshToken

VERIFICATION_TOKEN_MAX_AGE = timedelta(hours=24)

VERIFICATION_SALT = "teamflow.email-verification"


def generate_email_verification_token(user):
    signer = signing.TimestampSigner(
        salt=VERIFICATION_SALT,
    )

    return signer.sign(str(user.id))


def verify_email_verification_token(token):
    signer = signing.TimestampSigner(
        salt=VERIFICATION_SALT,
    )

    return signer.unsign(
        token,
        max_age=VERIFICATION_TOKEN_MAX_AGE,
    )


def activate_user_from_verification(user):
    if user.is_active:
        raise ValueError(
            "User is already verified."
        )

    user.is_active = True
    user.save(update_fields=["is_active"])

    return user

def send_verification_email(user, verification_url):
    send_mail(
        subject="Verify your TeamFlow account",
        message=(
            "Welcome to TeamFlow!\n\n"
            "Please verify your email address by opening this link:\n\n"
            f"{verification_url}\n\n"
            "This link expires after 24 hours."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

def resend_verification_email(user, verification_url):
    send_verification_email(
        user,
        verification_url,
    )

def generate_password_reset_token(user):
    return default_token_generator.make_token(user)

def generate_password_reset_uid(user):
    return urlsafe_base64_encode(
        force_bytes(user.id)
    )

def is_valid_password_reset_token(user, token):
    return default_token_generator.check_token(
        user,
        token,
    )

def reset_user_password(user, password):
    user.set_password(password)
    user.save(update_fields=["password"])

    return user

def send_password_reset_email(user, reset_url):
    send_mail(
        subject="Reset your TeamFlow password",
        message=(
            "We received a request to reset your password.\n\n"
            "Open the following link to choose a new password:\n\n"
            f"{reset_url}\n\n"
            "This link will expire after the configured timeout."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

def change_user_password(user, old_password, new_password):
    if not user.check_password(old_password):
        raise ValueError(
            "Current password is incorrect."
        )

    validate_password(
        new_password,
        user,
    )

    user.set_password(new_password)
    user.save(update_fields=["password"])

    return user

def blacklist_refresh_token(refresh_token):
    token = RefreshToken(refresh_token)
    token.blacklist()
