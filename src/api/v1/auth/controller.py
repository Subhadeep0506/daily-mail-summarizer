import os
import datetime
import uuid
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from .services import GoogleOAuth2Service
from src.schema.user import User, UserToken
from src.database.database import SessionLocal
from src.models.user import UserLogin


router = APIRouter()

CLIENT_SECRETS_FILE = "credentials.json"
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
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=request.url_for("oauth2callback"),
        )
        flow.fetch_token(code=code)

        google_oauth_service.creds = flow.credentials
        user = await google_oauth_service.save_credentials(db)

        return {
            "message": "Authorization successful.",
            "user_info": user
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during OAuth callback: {e}")


@router.get("/register")
async def authorize_gmail(request: Request):
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=request.url_for("oauth2callback"),
        )
        authorization_url, _ = flow.authorization_url(prompt="consent")
        return {"authorization_url": authorization_url}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating authorization URL: {e}"
        )

@router.post("/login")
async def login(user_login: UserLogin, db: Session = Depends(get_db)):
    try:
        user = await google_oauth_service.load_credentials(db, email=user_login.email)
        return {
            "message": "Authentication successful.",
            "user_info": user
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating authorization URL: {e}"
        )