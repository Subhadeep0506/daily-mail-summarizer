import os
import datetime
import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from src.gmail.gmail_client_api import GmailClient
from src.schema.user import User, UserToken
from src.database.database import SessionLocal


router = APIRouter()

CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]
REDIRECT_URI = "https://8089-subhadeep05-dailymailsu-3e1maq78avb.ws-us120.gitpod.io/auth/oauth2callback"

gmail_client = GmailClient()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/oauth2callback")
async def oauth2callback(code: str, db: Session = Depends(get_db)):
    """Handle the OAuth callback and save the token."""
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
        )
        flow.fetch_token(code=code)

        gmail_client.creds = flow.credentials
        await gmail_client.save_credentials(db)

        return {
            "message": "Authorization successful.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during OAuth callback: {e}")


@router.get("/authorize")
async def authorize_gmail():
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
        )
        authorization_url, _ = flow.authorization_url(prompt="consent")
        return {"authorization_url": authorization_url}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating authorization URL: {e}"
        )
