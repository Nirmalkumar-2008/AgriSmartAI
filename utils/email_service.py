"""
AgriSmartAI - Email Service Utility
Sends email notifications for user feedback and platform support inquiries via SMTP (Gmail TLS/SSL).
"""

import os
import socket
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple
from dotenv import load_dotenv

# Load environment variables from project root .env if present
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
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
    Sends an email notification for submitted feedback to the platform administrator via SMTP TLS/SSL.
    Supports Gmail App Passwords (with or without spaces), handles missing/invalid credentials gracefully,
    and logs useful diagnostics without exposing secrets.

    Returns:
        Tuple[bool, str]: (success_flag, status_message)
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()

    try:
        smtp_port = int(os.getenv("SMTP_PORT", "587").strip())
    except (ValueError, TypeError):
        smtp_port = 587

    # Support common sender environment variable names
    smtp_username = (
        os.getenv("SMTP_USERNAME")
        or os.getenv("SMTP_EMAIL")
        or os.getenv("SMTP_USER")
        or "agrismart.off@gmail.com"
    ).strip()

    # Support raw and cleaned password (handle 16-char Gmail App Passwords formatted with spaces)
    raw_password = os.getenv("SMTP_PASSWORD", "").strip()
    clean_password = raw_password.replace(" ", "") if raw_password else ""

    receiver_email = (
        os.getenv("FEEDBACK_RECEIVER")
        or os.getenv("FEEDBACK_RECIPIENT")
        or os.getenv("RECEIVER_EMAIL")
        or smtp_username
        or "agrismart.off@gmail.com"
    ).strip()

    # Detect missing or placeholder password
    placeholders = {
        "",
        "your_gmail_app_password",
        "your_gmail_app_password_here",
        "<gmail_app_password>",
        "your_app_password",
        "your_password",
        "placeholder",
        "none"
    }
    if not clean_password or clean_password.lower() in placeholders:
        err_msg = "SMTP_PASSWORD is not configured in environment (missing or placeholder value)."
        logger.warning("Email notification skipped: %s", err_msg)
        return False, err_msg

    logger.info("Attempting feedback email notification to %s via %s:%s...", receiver_email, smtp_host, smtp_port)

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"AgriSmartAI Platform <{smtp_username}>"
        msg["To"] = receiver_email
        msg["Reply-To"] = email.strip()
        msg["Subject"] = f"AgriSmartAI Feedback: {subject.strip()} [{category.strip()}]"

        plain_text = f"""AgriSmartAI Platform Support & Feedback
========================================
Timestamp : {timestamp.strip()}
Category  : {category.strip()}
Name      : {name.strip()}
Email     : {email.strip()}
Subject   : {subject.strip()}

Message:
{message.strip()}

========================================
Submitted via AgriSmartAI Contact & Feedback Form.
"""

        html_text = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #071426; color: #f1f5f9; padding: 24px; }}
    .container {{ max-width: 600px; margin: 0 auto; background-color: #0d2137; border-radius: 16px; border: 1px solid #1e3a5f; padding: 28px; }}
    .header {{ border-bottom: 1px solid #1e3a5f; padding-bottom: 16px; margin-bottom: 20px; }}
    .badge {{ display: inline-block; background-color: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700; }}
    .title {{ font-size: 20px; font-weight: 800; color: #ffffff; margin-top: 12px; margin-bottom: 4px; }}
    .field {{ margin-bottom: 14px; font-size: 13px; }}
    .label {{ color: #94a3b8; font-weight: 600; display: block; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
    .value {{ color: #f8fafc; background-color: #071426; padding: 8px 12px; border-radius: 8px; border: 1px solid #1e3a5f; }}
    .message-box {{ color: #f8fafc; background-color: #071426; padding: 14px; border-radius: 10px; border: 1px solid #1e3a5f; white-space: pre-wrap; line-height: 1.5; }}
    .footer {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #1e3a5f; font-size: 11px; color: #64748b; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="badge">{category.strip()}</span>
      <div class="title">New Platform Feedback Received</div>
      <div style="font-size: 12px; color: #94a3b8;">{timestamp.strip()}</div>
    </div>
    <div class="field">
      <span class="label">Sender Name</span>
      <div class="value">{name.strip()}</div>
    </div>
    <div class="field">
      <span class="label">Sender Email</span>
      <div class="value"><a href="mailto:{email.strip()}" style="color: #4ade80; text-decoration: none;">{email.strip()}</a></div>
    </div>
    <div class="field">
      <span class="label">Subject</span>
      <div class="value">{subject.strip()}</div>
    </div>
    <div class="field">
      <span class="label">Message</span>
      <div class="message-box">{message.strip()}</div>
    </div>
    <div class="footer">
      Sent from AgriSmartAI Decision Support System &bull; <a href="https://agrismartai-ms9q.onrender.com" style="color: #4ade80;">AgriSmartAI Live</a>
    </div>
  </div>
</body>
</html>
"""

        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_text, "html", "utf-8"))

        # Gmail SSL on port 465 or STARTTLS on port 587
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                server.login(smtp_username, clean_password)
                server.sendmail(smtp_username, [receiver_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_username, clean_password)
                server.sendmail(smtp_username, [receiver_email], msg.as_string())

        logger.info("Feedback email notification successfully dispatched to %s.", receiver_email)
        return True, "Email notification sent successfully."

    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Gmail SMTP authentication failed: Invalid credentials. "
            "Please ensure SMTP_USERNAME/SMTP_EMAIL is your sender Gmail address and SMTP_PASSWORD is a valid 16-character Gmail App Password."
        )
        return False, "SMTP authentication failed. Verify Gmail address and App Password configuration."

    except (smtplib.SMTPConnectError, ConnectionRefusedError, TimeoutError, socket.timeout) as e:
        logger.error("Gmail SMTP connection failed to %s:%s - %s", smtp_host, smtp_port, type(e).__name__)
        return False, f"Could not connect to SMTP server ({smtp_host}:{smtp_port})."

    except smtplib.SMTPException as e:
        logger.error("SMTP error during feedback email dispatch: %s", type(e).__name__)
        return False, f"SMTP protocol error: {type(e).__name__}"

    except Exception as e:
        logger.error("Unexpected error during feedback email dispatch: %s", type(e).__name__)
        return False, f"Unexpected error occurred during email delivery: {type(e).__name__}"
