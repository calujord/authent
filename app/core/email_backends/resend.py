"""
Resend Email Backend for Django
https://resend.com/docs/api-reference/emails/send-email
https://resend.com/docs/api-reference/batch/send-batch-emails

Soporta envio individual y batch (hasta 100 emails por llamada API).
"""

import logging

import resend
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

# Resend batch API limit
RESEND_BATCH_SIZE = 100


class ResendEmailBackend(BaseEmailBackend):
    """
    Email backend that uses Resend API to send emails.
    Automatically uses the Batch API when multiple messages are sent at once,
    reducing HTTP roundtrips significantly (e.g., 300 emails = 3 API calls
    instead of 300).
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, "RESEND_API_KEY", "")
        if self.api_key:
            resend.api_key = self.api_key
        else:
            logger.error("RESEND_API_KEY not found in settings")

    def _build_email_data(self, message):
        """
        Convert a Django EmailMessage into a Resend API payload dict.
        Returns None if the message cannot be built.
        """
        email_data = {
            "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
            "to": message.to,
            "subject": message.subject,
        }

        if message.cc:
            email_data["cc"] = message.cc
        if message.bcc:
            email_data["bcc"] = message.bcc

        # HTML content from alternatives
        if hasattr(message, "alternatives") and message.alternatives:
            for content, mimetype in message.alternatives:
                if mimetype == "text/html":
                    email_data["html"] = content
                    break
            if message.body:
                email_data["text"] = message.body
        else:
            email_data["text"] = message.body

        if message.reply_to:
            email_data["reply_to"] = message.reply_to

        # Attachments
        if message.attachments:
            attachments_list = []
            for attachment in message.attachments:
                if isinstance(attachment, tuple):
                    filename, content, mimetype = attachment
                    import base64

                    if isinstance(content, str):
                        content = content.encode("utf-8")
                    attachments_list.append(
                        {
                            "filename": filename,
                            "content": list(content),
                            "content_type": mimetype or "application/octet-stream",
                        }
                    )
            if attachments_list:
                email_data["attachments"] = attachments_list

        return email_data

    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number sent.

        Uses Resend Batch API when there are multiple messages, sending up to
        100 emails per API call. Falls back to individual sends for single
        messages or when batch fails.
        """
        if not email_messages:
            return 0

        if not self.api_key:
            logger.error("Cannot send emails: RESEND_API_KEY not configured")
            if not self.fail_silently:
                raise ValueError("RESEND_API_KEY not configured")
            return 0

        messages = list(email_messages)

        # Single message -- no need for batch overhead
        if len(messages) == 1:
            return 1 if self._send_single(messages[0]) else 0

        # Multiple messages -- use batch API in chunks of RESEND_BATCH_SIZE
        num_sent = 0
        for i in range(0, len(messages), RESEND_BATCH_SIZE):
            chunk = messages[i:i + RESEND_BATCH_SIZE]
            num_sent += self._send_batch(chunk)

        return num_sent

    def _send_single(self, message):
        """Send a single email via Resend API."""
        email_data = self._build_email_data(message)
        if not email_data:
            return False

        try:
            response = resend.Emails.send(email_data)
            logger.info(
                f"Email sent via Resend: to={email_data['to']}, "
                f"id={response.get('id', 'N/A')}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to send email via Resend: {type(e).__name__}: {e}",
                exc_info=True,
            )
            if not self.fail_silently:
                raise
            return False

    def _send_batch(self, messages):
        """
        Send a batch of emails via Resend Batch API.
        Falls back to individual sends if the batch call fails.
        """
        payloads = []
        for msg in messages:
            data = self._build_email_data(msg)
            if data:
                payloads.append(data)

        if not payloads:
            return 0

        try:
            response = resend.Batch.send(payloads)
            sent = len(response.get("data", payloads))
            logger.info(
                f"Batch sent {sent} emails via Resend "
                f"(chunk size: {len(payloads)})"
            )
            return sent
        except Exception as e:
            logger.warning(
                f"Resend Batch API failed ({type(e).__name__}: {e}), "
                f"falling back to individual sends"
            )
            # Fallback: send individually
            num_sent = 0
            for msg in messages:
                if self._send_single(msg):
                    num_sent += 1
            return num_sent
