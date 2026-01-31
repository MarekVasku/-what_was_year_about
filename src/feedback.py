"""
Feedback submission system with 3-tier fallback.
Encapsulates webhook, SMTP, and file logging logic.
"""

import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from config import FEEDBACK_LOG_PATH, FEEDBACK_RECEIVER_EMAIL, FEEDBACK_SUBMISSION_TIMEOUT


@dataclass
class FeedbackResult:
    """Result of feedback submission attempt."""

    success: bool
    method: str | None = None  # "webhook", "smtp", or None if only file saved
    message: str = ""
    error: str | None = None


class FeedbackSubmitter:
    """
    Handle feedback submission with 3-tier fallback strategy.

    Priority order:
    1. Webhook (Zapier → email) - works in Hugging Face Spaces
    2. SMTP (Gmail) - works in local/dev environments
    3. File logging - always works as backup
    """

    def __init__(
        self,
        webhook_url: str | None = None,
        smtp_email: str | None = None,
        smtp_password: str | None = None,
        receiver_email: str = FEEDBACK_RECEIVER_EMAIL,
        timeout: int = FEEDBACK_SUBMISSION_TIMEOUT,
    ):
        """
        Initialize feedback submitter.

        Args:
            webhook_url: Zapier webhook URL
            smtp_email: Gmail address for SMTP
            smtp_password: Gmail app password for SMTP
            receiver_email: Email address to receive feedback
            timeout: Request timeout in seconds (must be between 1 and 60)

        Raises:
            ValueError: If timeout is not within valid range
        """
        if not 1 <= timeout <= 60:
            raise ValueError(f"Timeout must be between 1 and 60 seconds, got {timeout}")

        self.webhook_url = webhook_url
        self.smtp_email = smtp_email
        self.smtp_password = smtp_password
        self.receiver_email = receiver_email
        self.timeout = timeout

    def submit(
        self,
        email_prefix: str,
        songs: str,
        ideas: str,
    ) -> FeedbackResult:
        """
        Submit feedback with automatic fallback.

        Args:
            email_prefix: User's email prefix (optional)
            songs: Song suggestions
            ideas: Improvement ideas

        Returns:
            FeedbackResult with status and method used
        """
        if not songs.strip() and not ideas.strip():
            return FeedbackResult(success=False, error="No feedback provided (both fields empty)")

        # Build feedback body
        body = self._build_body(email_prefix, songs, ideas)
        subject = self._build_subject(email_prefix)

        # Always save to file first (for reliability)
        file_saved = self._save_to_file(email_prefix, body)

        # Try webhook first
        if self.webhook_url:
            result = self._try_webhook(subject, body)
            if result.success:
                result.message = self._build_success_message(result.method, songs, ideas, file_saved)
                return result

        # Try SMTP second
        if self.smtp_email and self.smtp_password:
            result = self._try_smtp(subject, body)
            if result.success:
                result.message = self._build_success_message(result.method, songs, ideas, file_saved)
                return result

        # Both failed, but file was saved
        return FeedbackResult(
            success=True,
            method=None,
            message=self._build_fallback_message(file_saved, songs, ideas),
        )

    def _build_body(self, email_prefix: str, songs: str, ideas: str) -> str:
        """Build email body with structured feedback."""
        body = "New feedback received!\n\n"
        body += f"Email Prefix: {email_prefix.strip() if email_prefix else '(not provided)'}\n\n"

        if songs.strip():
            body += "=" * 50 + "\n"
            body += "🎵 SONG SUGGESTIONS FOR 2025:\n"
            body += "=" * 50 + "\n"
            body += songs.strip() + "\n\n"

        if ideas.strip():
            body += "=" * 50 + "\n"
            body += "💡 IMPROVEMENT IDEAS:\n"
            body += "=" * 50 + "\n"
            body += ideas.strip() + "\n\n"

        return body

    def _build_subject(self, email_prefix: str) -> str:
        """Build email subject."""
        subject = f"Music Chart Feedback - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        if email_prefix and email_prefix.strip():
            subject += f" | from: {email_prefix.strip()}"
        return subject

    def _try_webhook(self, subject: str, body: str) -> FeedbackResult:
        """Attempt to submit via webhook."""
        try:
            payload = {
                "to": self.receiver_email,
                "subject": subject,
                "body": body,
            }
            response = requests.post(self.webhook_url, json=payload, timeout=self.timeout)
            if response.status_code in (200, 201):
                return FeedbackResult(success=True, method="webhook")

            # Try form data as fallback
            response = requests.post(self.webhook_url, data=payload, timeout=self.timeout)
            if response.status_code in (200, 201):
                return FeedbackResult(success=True, method="webhook")

            return FeedbackResult(success=False, error=f"Webhook returned status {response.status_code}")
        except Exception as e:
            return FeedbackResult(success=False, error=f"Webhook error: {str(e)}")

    def _try_smtp(self, subject: str, body: str) -> FeedbackResult:
        """Attempt to submit via SMTP."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.smtp_email
            msg["To"] = self.receiver_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP("smtp.gmail.com", 587, timeout=self.timeout) as server:
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(msg)

            return FeedbackResult(success=True, method="SMTP")
        except Exception as e:
            return FeedbackResult(success=False, error=f"SMTP error: {str(e)}")

    def _save_to_file(self, email_prefix: str, body: str) -> bool:
        """Save feedback to file as permanent backup."""
        try:
            with open(FEEDBACK_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 60}\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Email Prefix: {email_prefix.strip() if email_prefix else '(none)'}\n")
                f.write(f"{'=' * 60}\n")
                f.write(body)
            return True
        except Exception as e:
            print(f"Warning: Failed to save feedback to file: {str(e)}")
            return False

    @staticmethod
    def _build_success_message(method: str, songs: str, ideas: str, file_saved: bool) -> str:
        """Build success response message."""
        message = f"✅ **Thank you!** Your feedback has been sent via {method}.\n\n"

        if songs.strip():
            message += f"**Songs suggested:** {len(songs.strip().splitlines())} lines\n"
        if ideas.strip():
            message += f"**Ideas shared:** {len(ideas.strip().splitlines())} lines\n"

        if not file_saved:
            message += "\n⚠️ Warning: Could not save to backup file."

        return message

    @staticmethod
    def _build_fallback_message(file_saved: bool, songs: str, ideas: str) -> str:
        """Build fallback message when no email method worked."""
        message = "✅ **Thank you!** Your feedback has been saved.\n\n"
        message += "ℹ️ Email notification unavailable (configure WEBHOOK_URL or SMTP).\n\n"

        if songs.strip():
            message += f"**Songs suggested:** {len(songs.strip().splitlines())} lines\n"
        if ideas.strip():
            message += f"**Ideas shared:** {len(ideas.strip().splitlines())} lines\n"

        if not file_saved:
            message += "\n⚠️ Warning: Could not save to backup file."

        return message
