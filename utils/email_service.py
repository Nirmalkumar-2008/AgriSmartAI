"""
AgriSmartAI - Email Service Utility
Sends email notifications for user feedback and platform support inquiries via SMTP TLS.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple
from dotenv import load_dotenv

# Load environment variables
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
    Sends an email notification for submitted feedback to agrismart.off@gmail.com via SMTP TLS.
    Sets Reply-To to the submitted user's email address.
    Returns (success_flag, status_message).
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "agrismart.off@gmail.com").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    receiver_email = os.getenv("FEEDBACK_RECEIVER", "agrismart.off@gmail.com").strip()

    if not smtp_password or smtp_password in ["YOUR_GMAIL_APP_PASSWORD", "your_gmail_app_password_here", "<GMAIL_APP_PASSWORD>"]:
        err_msg = "SMTP_PASSWORD is not configured in .env file (placeholder value found)."
        logger.warning(f"Email notification failed: {err_msg}")
        return False, err_msg

    print("Attempting email notification...")
    logger.info("Attempting email notification...")

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"AgriSmartAI System <{smtp_username}>"
        msg["To"] = receiver_email
        msg["Reply-To"] = email.strip()
        msg["Subject"] = f"AgriSmartAI Feedback: {subject.strip()}"

        body_text = f"""AgriSmartAI Platform Feedback

Name:
{name.strip()}

Email:
{email.strip()}

Category:
{category.strip()}

Subject:
{subject.strip()}

Message:
{message.strip()}

Submitted:
{timestamp.strip()}

This message was submitted through the AgriSmartAI Contact / Feedback page.
"""
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, [receiver_email], msg.as_string())

        print("Email notification sent successfully")
        logger.info("Email notification sent successfully")
        return True, "Email notification sent successfully."

    except Exception as e:
        err_details = str(e)
        print(f"Email notification failed: {err_details}")
        logger.error(f"Email notification failed: {err_details}")
        return False, f"Email notification failed: {err_details}"
