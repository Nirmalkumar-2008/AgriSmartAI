
"""
AgriSmartAI - Email Service Utility
Sends feedback notifications through the Resend HTTPS API.
"""

import os
import logging
from html import escape
from typing import Tuple

import resend
from dotenv import load_dotenv

# Load environment variables from the project root.
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
load_dotenv(os.path.join(project_root, ".env"))

logger = logging.getLogger("AgriSmartAI.EmailService")


def send_feedback_email(
    name: str,
    email: str,
    subject: str,
    category: str,
    message: str,
    timestamp: str
) -> Tuple[bool, str]:
    """
    Send a feedback notification using Resend.

    Returns:
        (success_flag, status_message)
    """
    api_key = os.getenv("RESEND_API_KEY", "").strip()

    if not api_key:
        logger.warning(
            "Email notification skipped: RESEND_API_KEY is missing."
        )
        return False, "Resend API key is not configured."

    sender = os.getenv(
        "RESEND_FROM_EMAIL", "onboarding@resend.dev"
    ).strip()

    receiver = (
        os.getenv("FEEDBACK_RECEIVER")
        or os.getenv("FEEDBACK_RECIPIENT")
        or os.getenv("RECEIVER_EMAIL")
        or os.getenv("SMTP_USERNAME")
        or "agrismart.off@gmail.com"
    ).strip()

    if not sender or not receiver:
        logger.warning("Email notification skipped: sender or receiver missing.")
        return False, "Email sender or receiver is not configured."

    # Escape user-submitted values before inserting them into HTML.
    safe_name = escape(name.strip())
    safe_email = escape(email.strip(), quote=True)
    safe_subject = escape(subject.strip())
    safe_category = escape(category.strip())
    safe_timestamp = escape(timestamp.strip())
    safe_message = escape(message.strip())

    plain_text = f"""AgriSmartAI Platform Support & Feedback
========================================
Timestamp: {timestamp.strip()}
Category: {category.strip()}
Name: {name.strip()}
Email: {email.strip()}
Subject: {subject.strip()}

Message:
{message.strip()}

Submitted through the AgriSmartAI feedback form.
"""

    html_text = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#071426;color:#f1f5f9;padding:24px">
  <div style="max-width:600px;margin:auto;background:#0d2137;border-radius:12px;padding:24px">
    <h2>New AgriSmartAI Feedback</h2>
    <p><strong>Category:</strong> {safe_category}</p>
    <p><strong>Timestamp:</strong> {safe_timestamp}</p>
    <p><strong>Name:</strong> {safe_name}</p>
    <p><strong>Email:</strong>
      <a href="mailto:{safe_email}">{safe_email}</a>
    </p>
    <p><strong>Subject:</strong> {safe_subject}</p>
    <p><strong>Message:</strong></p>
    <div style="white-space:pre-wrap;background:#071426;padding:14px;border-radius:8px">{safe_message}</div>
    <p style="margin-top:24px">
      Sent from AgriSmartAI Decision Support System.
      <a href="https://agrismartai-ms9q.onrender.com">Visit AgriSmartAI</a>
    </p>
  </div>
</body>
</html>
"""

    try:
        resend.api_key = api_key

        params = {
            "from": f"AgriSmartAI Platform <{sender}>",
            "to": [receiver],
            "reply_to": email.strip(),
            "subject": f"AgriSmartAI Feedback: {subject.strip()} [{category.strip()}]",
            "text": plain_text,
            "html": html_text,
        }

        result = resend.Emails.send(params)

        if isinstance(result, dict):
            email_id = result.get("id")
        else:
            email_id = getattr(result, "id", None)

        logger.info(
            "Resend accepted feedback email request. Email ID: %s",
            email_id or "not returned"
        )
        return True, "Email notification sent successfully."

    except Exception as exc:
        # Avoid logging API keys, message contents, or full exception details.
        logger.error(
            "Resend feedback email failed (%s).",
            type(exc).__name__
        )
        return False, f"Email delivery failed ({type(exc).__name__})."
