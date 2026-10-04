import os
import sqlite3
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
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

    print(f"Feedback received from user: {payload.name.strip()} ({payload.email.strip()})")
    logger.info(f"Feedback received from user: {payload.name.strip()} ({payload.email.strip()})")

    # Step 1: Save feedback to SQLite database
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
        
        print("Feedback saved to database")
        logger.info("Feedback saved to database")
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
        return {
            "success": True,
            "database_saved": True,
            "email_sent": True,
            "message": "Feedback submitted successfully.",
            "feedback_id": feedback_id,
            "timestamp": timestamp
        }
    else:
        return {
            "success": True,
            "database_saved": True,
            "email_sent": False,
            "message": "Feedback was saved successfully, but email delivery failed.",
            "feedback_id": feedback_id,
            "timestamp": timestamp
        }

@router.get("/feedback", response_model=List[FeedbackResponse])
def get_all_feedback():
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
