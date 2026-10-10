"""Django email backend that sends transactional mail via SendGrid's HTTP API."""

import base64
from email.utils import parseaddr

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend
from sendgrid import SendGridAPIClient


def _address(value):
    name, address = parseaddr(value or "")
    address = address or (value or "").strip()
    result = {"email": address}
    if name:
        result["name"] = name
    return result


class SendGridAPIEmailBackend(BaseEmailBackend):
    """Send Django EmailMessage instances through SendGrid Web API v3."""

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        api_key = getattr(settings, "SENDGRID_API_KEY", "")
        if not api_key:
            raise ImproperlyConfigured(
                "SENDGRID_API_KEY is missing. Add it to the environment variables."
            )

        client = SendGridAPIClient(api_key=api_key)
        sent_count = 0

        for message in email_messages:
            to = [_address(value) for value in (message.to or [])]
            cc = [_address(value) for value in (message.cc or [])]
            bcc = [_address(value) for value in (message.bcc or [])]

            if not (to or cc or bcc):
                continue

            from_value = message.from_email or getattr(settings, "DEFAULT_FROM_EMAIL", "")
            sender = _address(from_value)
            if not sender.get("email"):
                raise ImproperlyConfigured(
                    "DEFAULT_FROM_EMAIL must be set to the verified SendGrid sender address."
                )

            personalization = {}
            if to:
                personalization["to"] = to
            if cc:
                personalization["cc"] = cc
            if bcc:
                personalization["bcc"] = bcc

            content_type = getattr(message, "content_subtype", "plain") or "plain"
            payload = {
                "personalizations": [personalization],
                "from": sender,
                "subject": message.subject or "",
                "content": [
                    {
                        "type": f"text/{content_type}",
                        "value": message.body or "",
                    }
                ],
            }

            # Preserve HTML/plain-text alternatives (e.g. EmailMultiAlternatives).
            for alternative in getattr(message, "alternatives", []) or []:
                if hasattr(alternative, "content"):
                    alt_content = alternative.content
                    alt_mimetype = alternative.mimetype
                else:
                    alt_content, alt_mimetype = alternative
                payload["content"].append(
                    {
                        "type": alt_mimetype or "text/html",
                        "value": alt_content or "",
                    }
                )

            reply_to = getattr(message, "reply_to", None) or []
            if reply_to:
                payload["reply_to"] = _address(reply_to[0])

            headers = getattr(message, "extra_headers", None) or {}
            if headers:
                payload["headers"] = {str(key): str(value) for key, value in headers.items()}

            attachments = []
            for attachment in getattr(message, "attachments", []) or []:
                if hasattr(attachment, "filename") and hasattr(attachment, "content"):
                    filename = attachment.filename
                    content = attachment.content
                    mimetype = attachment.mimetype
                elif isinstance(attachment, tuple):
                    filename, content, mimetype = attachment
                else:
                    filename = attachment.get_filename() or "attachment"
                    content = attachment.get_payload(decode=True) or b""
                    mimetype = attachment.get_content_type()

                if isinstance(content, str):
                    content = content.encode("utf-8")
                attachments.append(
                    {
                        "content": base64.b64encode(content).decode("ascii"),
                        "filename": filename or "attachment",
                        "type": mimetype or "application/octet-stream",
                        "disposition": "attachment",
                    }
                )

            if attachments:
                payload["attachments"] = attachments

            response = client.client.mail.send.post(request_body=payload)
            if not 200 <= response.status_code < 300:
                response_body = response.body
                if isinstance(response_body, bytes):
                    response_body = response_body.decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"SendGrid rejected the email with HTTP {response.status_code}: {response_body}"
                )

            sent_count += 1

        return sent_count
