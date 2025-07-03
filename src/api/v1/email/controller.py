import os
import datetime
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from src.gmail.gmail_client_api import GmailClient
from src.schema.user import User, UserToken
from src.database.database import SessionLocal


router = APIRouter()

CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = [os.getenv("GMAIL_SCOPE")]
REDIRECT_URI = os.getenv(
    "GMAIL_REDIRECT_URI", "http://localhost:8089/auth/oauth2callback"
)

gmail_client = GmailClient()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/emails")
async def get_emails(
    start_date: str = Query(..., description="Start date in YYYY/MM/DD format"),
    end_date: str = Query(..., description="End date in YYYY/MM/DD format"),
    db: Session = Depends(get_db)
):
    """Fetch emails within a date range."""
    try:
        emails = await gmail_client.read_emails_for_date(start_date, end_date, db)
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching emails: {e}")
