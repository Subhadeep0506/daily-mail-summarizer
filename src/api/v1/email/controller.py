import os
import datetime
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from .services import GmailService
from ..auth.services import GoogleOAuth2Service
from src.schema.user import User, UserToken
from src.database.database import SessionLocal


router = APIRouter()

CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = [os.getenv("GMAIL_SCOPE")]
REDIRECT_URI = os.getenv(
    "GMAIL_REDIRECT_URI", "http://localhost:8089/auth/oauth2callback"
)

google_auth = GoogleOAuth2Service()
gmail_client = GmailService(google_auth)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/emails")
async def get_emails(
    access_token: str = Query(..., description="Access token for authentication"),
    start_date: str = Query(..., description="Start date in YYYY/MM/DD format"),
    end_date: str = Query(..., description="End date in YYYY/MM/DD format"),
    db: Session = Depends(get_db)
):
    """Fetch emails within a date range."""
    try:
        emails = await gmail_client.read_emails_for_date(access_token, start_date, end_date, db)
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching emails: {e}")
