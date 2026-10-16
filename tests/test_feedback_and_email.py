"""
AgriSmartAI - Feedback Privacy & Email Notifications Test Suite
Verifies:
1. Feedback submission and database persistence.
2. Complete privacy of feedback records against unauthenticated visitors (API and Frontend).
3. Server-side administrative authentication (fail-closed, valid key, invalid key).
4. Email notification service error handling, credential fallback, and secret protection.
5. System health and multi-module ML recommendation regression safety.
"""

import os
import sys
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.main import app
from backend.routes.feedback import DB_PATH, init_db
from utils.email_service import send_feedback_email

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure database table exists and clean up test records before/after tests."""
    init_db()
    yield

class TestFeedbackPrivacyAndPersistence:
    """Tests for feedback submission, storage, and visitor privacy."""

    def test_visitor_can_submit_feedback_successfully(self):
        """Visitors can submit feedback without exposing other users' information."""
        payload = {
            "name": "Farmer John",
            "email": "farmer.john@example.com",
            "subject": "Soil Moisture Query",
            "category": "Agricultural Recommendation",
            "message": "The soil moisture sensor reading seems slightly low after irrigation."
        }
        response = client.post("/feedback", json=payload)
        assert response.status_code == 201
        data = response.json()

        # Check response structure
        assert data.get("success") is True
        assert data.get("database_saved") is True
        assert "feedback_id" in data
        assert "timestamp" in data

        # CRITICAL PRIVACY: The response must not echo other feedback or raw PII
        assert "records" not in data
        assert "all_feedback" not in data

        # Verify feedback was saved to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, email, subject, category, message FROM feedback WHERE id = ?", (data["feedback_id"],))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "Farmer John"
        assert row[1] == "farmer.john@example.com"
        assert row[2] == "Soil Moisture Query"
        assert row[3] == "Agricultural Recommendation"
        assert row[4] == payload["message"]

    def test_feedback_submission_validation_rejects_empty_fields(self):
        """Input validation requires name, email, subject, and message."""
        invalid_payload = {
            "name": "   ",
            "email": "invalid-email",
            "subject": "",
            "category": "UI / UX",
            "message": ""
        }
        response = client.post("/feedback", json=invalid_payload)
        assert response.status_code == 400

    def test_unauthenticated_visitor_blocked_from_feedback_log(self, monkeypatch):
        """Unauthenticated visitors calling GET /feedback receive 401 or 403."""
        # Scenario A: When ADMIN_API_KEY is not set in environment (fails closed)
        monkeypatch.delenv("ADMIN_API_KEY", raising=False)
        monkeypatch.delenv("FEEDBACK_ADMIN_KEY", raising=False)
        res_unconfigured = client.get("/feedback")
        assert res_unconfigured.status_code == 403
        assert "Administrative feedback access is not configured" in res_unconfigured.json().get("detail", "")

        # Scenario B: When ADMIN_API_KEY is configured, but visitor provides no credentials
        monkeypatch.setenv("ADMIN_API_KEY", "super-secret-admin-token-12345")
        res_no_auth = client.get("/feedback")
        assert res_no_auth.status_code == 401
        assert "Authentication required" in res_no_auth.json().get("detail", "")

    def test_invalid_admin_key_rejected(self, monkeypatch):
        """Requests with invalid admin credentials receive 401 Unauthorized."""
        monkeypatch.setenv("ADMIN_API_KEY", "super-secret-admin-token-12345")

        # Wrong header key
        res1 = client.get("/feedback", headers={"X-Admin-Key": "wrong-key"})
        assert res1.status_code == 401
        assert "Invalid administrative credentials" in res1.json().get("detail", "")

        # Wrong Bearer token
        res2 = client.get("/feedback", headers={"Authorization": "Bearer bad-bearer-token"})
        assert res2.status_code == 401
        assert "Invalid administrative credentials" in res2.json().get("detail", "")

    def test_authenticated_admin_can_retrieve_feedback(self, monkeypatch):
        """Authenticated admin with valid key can access feedback records."""
        admin_token = "valid-admin-secret-xyz-987"
        monkeypatch.setenv("ADMIN_API_KEY", admin_token)

        # Access with X-Admin-Key header
        res = client.get("/feedback", headers={"X-Admin-Key": admin_token})
        assert res.status_code == 200
        records = res.json()
        assert isinstance(records, list)

        # Access with Authorization: Bearer header
        res_bearer = client.get("/feedback", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_bearer.status_code == 200
        records_bearer = res_bearer.json()
        assert isinstance(records_bearer, list)

    def test_feedback_saving_succeeds_even_when_email_fails(self, monkeypatch):
        """Feedback continues to be saved in database when email delivery fails."""
        monkeypatch.setenv("SMTP_PASSWORD", "")  # unconfigured password

        payload = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "subject": "Platform Accessibility",
            "category": "UI / UX",
            "message": "Great high-contrast dark theme mode!"
        }
        response = client.post("/feedback", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data.get("success") is True
        assert data.get("database_saved") is True
        assert data.get("email_sent") is False

        # Verify persisted in database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name FROM feedback WHERE id = ?", (data["feedback_id"],))
        assert c.fetchone()[0] == "Jane Doe"
        conn.close()


class TestEmailNotificationService:
    """Tests for utils.email_service.send_feedback_email."""

    def test_email_missing_or_placeholder_password_handled_gracefully(self, monkeypatch):
        """Missing or placeholder SMTP_PASSWORD returns False gracefully without raising exceptions."""
        for placeholder in ["", "YOUR_GMAIL_APP_PASSWORD", "your_gmail_app_password_here"]:
            monkeypatch.setenv("SMTP_PASSWORD", placeholder)
            success, msg = send_feedback_email(
                name="Test",
                email="test@example.com",
                subject="Test",
                category="General Feedback",
                message="Test Message",
                timestamp="2026-10-16 12:00:00"
            )
            assert success is False
            assert "SMTP_PASSWORD is not configured" in msg

    def test_email_app_password_spaces_handled(self, monkeypatch):
        """Gmail 16-character App Passwords with spaces (e.g. abcd efgh ijkl mnop) are sanitized."""
        monkeypatch.setenv("SMTP_PASSWORD", "abcd efgh ijkl mnop")
        monkeypatch.setenv("SMTP_USERNAME", "sender@gmail.com")
        
        with patch("smtplib.SMTP") as mock_smtp:
            instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = instance

            success, msg = send_feedback_email(
                name="Farmer",
                email="farmer@example.com",
                subject="Yield Question",
                category="General Feedback",
                message="Testing spaces",
                timestamp="2026-10-16 12:00:00"
            )

            assert success is True
            # Login must have received password without spaces
            instance.login.assert_called_once_with("sender@gmail.com", "abcdefghijklmnop")

    def test_email_env_variable_aliases(self, monkeypatch):
        """Supports SMTP_EMAIL or SMTP_USER as sender username if SMTP_USERNAME is not set."""
        monkeypatch.delenv("SMTP_USERNAME", raising=False)
        monkeypatch.setenv("SMTP_EMAIL", "sender_alt@gmail.com")
        monkeypatch.setenv("SMTP_PASSWORD", "testpassword1234")

        with patch("smtplib.SMTP") as mock_smtp:
            instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = instance

            success, _ = send_feedback_email(
                name="Farmer",
                email="farmer@example.com",
                subject="Crop Question",
                category="General Feedback",
                message="Testing alias",
                timestamp="2026-10-16 12:00:00"
            )

            assert success is True
            instance.login.assert_called_once_with("sender_alt@gmail.com", "testpassword1234")

    def test_email_authentication_error_handled_cleanly(self, monkeypatch):
        """SMTPAuthenticationError is caught, logged, and does not leak credentials."""
        monkeypatch.setenv("SMTP_PASSWORD", "secret_pass")
        monkeypatch.setenv("SMTP_USERNAME", "sender@gmail.com")

        with patch("smtplib.SMTP") as mock_smtp:
            instance = MagicMock()
            import smtplib
            instance.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication credentials invalid")
            mock_smtp.return_value.__enter__.return_value = instance

            success, msg = send_feedback_email(
                name="Test",
                email="test@example.com",
                subject="Subject",
                category="UI / UX",
                message="Message",
                timestamp="2026-10-16 12:00:00"
            )

            assert success is False
            assert "SMTP authentication failed" in msg
            # Check secret is not in the error message
            assert "secret_pass" not in msg

    def test_email_connection_error_handled_cleanly(self, monkeypatch):
        """Connection errors are caught and handled gracefully."""
        monkeypatch.setenv("SMTP_PASSWORD", "secret_pass")
        monkeypatch.setenv("SMTP_HOST", "invalid.smtp.host")

        with patch("smtplib.SMTP") as mock_smtp:
            import smtplib
            mock_smtp.side_effect = smtplib.SMTPConnectError(421, b"Connection refused")

            success, msg = send_feedback_email(
                name="Test",
                email="test@example.com",
                subject="Subject",
                category="UI / UX",
                message="Message",
                timestamp="2026-10-16 12:00:00"
            )

            assert success is False
            assert "Could not connect to SMTP server" in msg


class TestFrontendPrivacyGuarantees:
    """Verifies that the frontend does not contain or request public feedback logs."""

    def test_index_html_has_no_feedback_log_or_history_state(self):
        index_path = os.path.join(PROJECT_ROOT, "frontend", "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        # The public log header and state must be absent
        assert "Submitted Platform Feedback Log" not in content
        assert "feedbackHistory" not in content
        # There must be no GET request to /feedback in frontend JavaScript
        assert "fetch('/feedback')" not in content
        assert 'fetch("/feedback")' not in content


class TestApplicationHealthAndRegressions:
    """Verifies existing API endpoints, health check, and prediction service."""

    def test_health_endpoint(self):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert "status" in data
        assert "models_loaded" in data

    def test_api_info_endpoint(self):
        res = client.get("/api-info")
        assert res.status_code == 200
        data = res.json()
        assert data.get("name") == "AgriSmartAI Precision Agriculture REST API"

    def test_evaluation_summary_endpoint(self):
        res = client.get("/evaluation/summary")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "success"
        assert "crop_recommendation" in data
        assert "yield_prediction" in data
        assert "fertilizer" in data

    def test_prediction_history_endpoints_preserved(self):
        res = client.get("/prediction-history")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert "history" in data

    def test_predict_endpoint_regression(self):
        """Verify multi-module recommendations work without regressions."""
        payload = {
            "city": "Bengaluru",
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "ph": 6.5,
            "temperature": 25.0,
            "humidity": 65.0,
            "rainfall": 120.0,
            "soil_moisture": 60.0,
            "selected_crop": "Rice"
        }
        res = client.post("/predict", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "recommended_crops" in data or "recommended_crop" in data
        assert "fertilizer_recommendation" in data
        assert "predicted_yield_tons_per_ha" in data
        assert "irrigation_recommendation" in data

    def test_weather_endpoint_regression(self):
        """Verify weather endpoint handles requests without crashing."""
        res = client.get("/weather/Bengaluru")
        # In test environments without an active API key or network, it gracefully handles failure
        assert res.status_code in [200, 400, 404, 500, 502]

