import datetime
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from src.database.database import SessionLocal
from src.models.user import UserLogin
from src.schema.user import User, UserToken

from .services import GoogleOAuth2Service

router = APIRouter()

CLIENT_SECRETS_FILE = "credentials.json"
CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "project_id": os.getenv("GOOGLE_PROJECT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uris": [
            "http://localhost",
            "https://8089-subhadeep05-dailymailsu-3e1maq78avb.ws-us120.gitpod.io",
        ],
    }
}
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

google_oauth_service = GoogleOAuth2Service()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/oauth2callback")
async def oauth2callback(code: str, request: Request, db: Session = Depends(get_db)):
    """Handle the OAuth callback and save the token."""
    try:
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=request.url_for("oauth2callback"),
        )
        flow.fetch_token(code=code)

        google_oauth_service.creds = flow.credentials
        token_info = await google_oauth_service.save_credentials(db)

        return {"message": "Authorization successful.", **token_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during OAuth callback: {e}")


@router.get("/authorize")
async def authorize_gmail(request: Request):
    try:
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=request.url_for("oauth2callback"),
        )
        authorization_url, _ = flow.authorization_url(
            access_type="offline", prompt="consent"
        )
        return {"authorization_url": authorization_url}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating authorization URL: {e}"
        )
