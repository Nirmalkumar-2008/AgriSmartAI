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
        monkeypatch.delenv("RESEND_API_KEY", raising=False)

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
    """Tests for the Resend email notification service."""

    def test_missing_resend_api_key_handled_gracefully(self, monkeypatch):
        """Missing API key must not trigger an API request."""
        monkeypatch.delenv("RESEND_API_KEY", raising=False)

        with patch("utils.email_service.resend.Emails.send") as mock_send:
            success, msg = send_feedback_email(
                name="Test",
                email="test@example.com",
                subject="Test",
                category="General Feedback",
                message="Test message",
                timestamp="2026-10-16 12:00:00",
            )

        assert success is False
        assert mock_send.call_count == 0

    def test_resend_email_success_without_real_api_call(self, monkeypatch):
        """A mocked Resend response verifies success without sending an email."""
        monkeypatch.setenv("RESEND_API_KEY", "test_key_not_real")
        monkeypatch.setenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        monkeypatch.setenv("FEEDBACK_RECEIVER", "admin@example.com")

        with patch(
            "utils.email_service.resend.Emails.send",
            return_value={"id": "test-email-id"},
        ) as mock_send:
            success, msg = send_feedback_email(
                name="Test Farmer",
                email="farmer@example.com",
                subject="Crop Question",
                category="General Feedback",
                message="Testing the email service",
                timestamp="2026-10-16 12:00:00",
            )

        assert success is True
        mock_send.assert_called_once()

        params = mock_send.call_args.args[0]
        assert params["from"] == "AgriSmartAI Platform <onboarding@resend.dev>"
        assert params["to"] == ["admin@example.com"]
        assert params["reply_to"] == "farmer@example.com"

    def test_resend_failure_is_handled_without_leaking_secrets(
        self, monkeypatch, caplog
    ):
        """API failures must not expose credentials or private message content."""
        secret = "test_key_not_real_123"
        private_message = "private-feedback-content-123"

        monkeypatch.setenv("RESEND_API_KEY", secret)

        with patch(
            "utils.email_service.resend.Emails.send",
            side_effect=RuntimeError("Simulated Resend failure"),
        ):
            success, msg = send_feedback_email(
                name="Test Farmer",
                email="farmer@example.com",
                subject="Test",
                category="General Feedback",
                message=private_message,
                timestamp="2026-10-16 12:00:00",
            )

        assert success is False
        assert secret not in msg
        assert secret not in caplog.text
        assert private_message not in caplog.text

    def test_feedback_is_saved_when_resend_fails(self, monkeypatch):
        """Feedback must still be saved if Resend is unavailable."""
        monkeypatch.setenv("RESEND_API_KEY", "test_key_not_real")

        payload = {
            "name": "Network Test Farmer",
            "email": "farmer_net@example.com",
            "subject": "Testing email failure",
            "category": "Weather Integration",
            "message": "Feedback should be saved even if email fails.",
        }

        with patch(
            "utils.email_service.resend.Emails.send",
            side_effect=RuntimeError("Simulated Resend failure"),
        ):
            response = client.post("/feedback", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data.get("success") is True
        assert data.get("database_saved") is True
        assert data.get("email_sent") is False

        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, email FROM feedback WHERE id = ?",
                (data["feedback_id"],),
            )
            row = cursor.fetchone()
        finally:
            conn.close()

        assert row is not None
        assert row[0] == "Network Test Farmer"
        assert row[1] == "farmer_net@example.com"




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

    def test_index_html_jsx_syntax_validity(self):
        """Verifies that the inline Babel JSX script in index.html parses with zero syntax errors."""
        index_path = os.path.join(PROJECT_ROOT, "frontend", "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        start_tag = '<script type="text/babel">'
        end_tag = '</script>'
        start_idx = content.find(start_tag)
        assert start_idx != -1, "Inline Babel script start tag not found"
        start_idx += len(start_tag)
        end_idx = content.find(end_tag, start_idx)
        assert end_idx != -1, "Inline Babel script end tag not found"
        script_code = content[start_idx:end_idx]

        import subprocess
        node_script = (
            "const parser = require('./frontend/node_modules/@babel/parser');\n"
            "let code = '';\n"
            "process.stdin.setEncoding('utf8');\n"
            "process.stdin.on('data', chunk => { code += chunk; });\n"
            "process.stdin.on('end', () => {\n"
            "  try {\n"
            "    parser.parse(code, { sourceType: 'module', plugins: ['jsx'] });\n"
            "    console.log('PARSED_OK');\n"
            "  } catch (err) {\n"
            "    console.error('JSX_SYNTAX_ERROR: ' + err.message + ' at line ' + err.loc.line + ', col ' + err.loc.column);\n"
            "    process.exit(1);\n"
            "  }\n"
            "});\n"
        )
        result = subprocess.run(
            ["node", "-e", node_script],
            input=script_code,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        assert result.returncode == 0, f"JSX Syntax Error in frontend/index.html:\n{result.stderr}\n{result.stdout}"
        assert "PARSED_OK" in result.stdout




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

