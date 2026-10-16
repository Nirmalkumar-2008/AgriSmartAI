import os
import sqlite3
import logging
import secrets
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Header, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List
from utils.email_service import send_feedback_email

logger = logging.getLogger("AgriSmartAI.FeedbackRoute")

router = APIRouter(prefix="", tags=["Feedback"])

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feedback.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            category TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Administrative Access Security
security_bearer = HTTPBearer(auto_error=False)

def verify_admin_access(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    auth: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> bool:
    """
    Enforces server-side authentication for administrative access to feedback records.
    Requires ADMIN_API_KEY or FEEDBACK_ADMIN_KEY in environment variables.
    If no admin key is configured, access is rejected (403 Forbidden) so that
    no unauthenticated, default, or accidental exposure can occur.
    """
    admin_secret = os.getenv("ADMIN_API_KEY") or os.getenv("FEEDBACK_ADMIN_KEY")
    if not admin_secret or not admin_secret.strip():
        logger.warning("Feedback access attempted, but no administrative key (ADMIN_API_KEY) is configured on this server.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative feedback access is not configured on this server."
        )

    provided_key = None
    if x_admin_key and x_admin_key.strip():
        provided_key = x_admin_key.strip()
    elif auth and auth.credentials and auth.credentials.strip():
        provided_key = auth.credentials.strip()

    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid administrative key via 'X-Admin-Key' header or 'Authorization: Bearer <key>'.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not secrets.compare_digest(provided_key, admin_secret.strip()):
        logger.warning("Failed administrative feedback access attempt with invalid credentials.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return True

class FeedbackRequest(BaseModel):
    name: str = Field(..., max_length=100)
    email: str = Field(..., max_length=150)
    subject: str = Field(..., max_length=200)
    category: Optional[str] = Field("General Feedback", max_length=100)
    message: str = Field(..., max_length=5000)

class FeedbackResponse(BaseModel):
    id: int
    timestamp: str
    name: str
    email: str
    subject: str
    category: str
    message: str

@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(payload: FeedbackRequest):
    if not payload.name.strip() or not payload.email.strip() or not payload.subject.strip() or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Name, email, subject, and message are required.")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    category = payload.category.strip() if payload.category else "General Feedback"

    logger.info("Feedback submission received (category: %s)", category)

    # Step 1: Save feedback to SQLite database safely
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO feedback (timestamp, name, email, subject, category, message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, payload.name.strip(), payload.email.strip(), payload.subject.strip(), category, payload.message.strip()))
        conn.commit()
        feedback_id = cursor.lastrowid
        conn.close()

        logger.info("Feedback successfully saved to database (ID: %s)", feedback_id)
    except Exception as e:
        logger.error(f"Database error while saving feedback: {e}")
        raise HTTPException(status_code=500, detail="Database storage failed.")

    # Step 2: Attempt email notification via SMTP TLS
    email_sent, email_msg = send_feedback_email(
        name=payload.name.strip(),
        email=payload.email.strip(),
        subject=payload.subject.strip(),
        category=category,
        message=payload.message.strip(),
        timestamp=timestamp
    )

    if email_sent:
        logger.info("Feedback (ID: %s) processed and notification email sent.", feedback_id)
        return {
            "success": True,
            "database_saved": True,
            "email_sent": True,
            "message": "Feedback submitted successfully.",
            "feedback_id": feedback_id,
            "timestamp": timestamp
        }
    else:
        logger.warning("Feedback (ID: %s) saved to database, but notification email was not sent: %s", feedback_id, email_msg)
        return {
            "success": True,
            "database_saved": True,
            "email_sent": False,
            "message": "Feedback was saved successfully, but email delivery failed.",
            "feedback_id": feedback_id,
            "timestamp": timestamp
        }

@router.get("/feedback", response_model=List[FeedbackResponse])
@router.get("/admin/feedback", response_model=List[FeedbackResponse], include_in_schema=False)
def get_all_feedback(_: bool = Depends(verify_admin_access)):
    """
    Administrative endpoint to retrieve submitted feedback records.
    Protected by server-side authentication (verify_admin_access).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, name, email, subject, category, message FROM feedback ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "timestamp": r[1],
            "name": r[2],
            "email": r[3],
            "subject": r[4],
            "category": r[5],
            "message": r[6]
        }
        for r in rows
    ]
