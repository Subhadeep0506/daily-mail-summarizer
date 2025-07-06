import base64
import json
import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from src.core.logger import SingletonLogger
from src.database.database import SessionLocal
from src.models.token import UserToken as UserTokenModel
from src.models.user import User as UserModel
from src.schema.user import User, UserToken

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


class GoogleOAuth2Service:
    """Handles authentication and credential management."""

    def __init__(self):
        self.logger = SingletonLogger().logger
        self.email = None
        self.creds = None

    async def load_credentials(self, access_token: str, db: Session):
        """Load credentials from the database or initiate OAuth flow."""
        try:
            user_token = (
                db.query(UserToken).filter(UserToken.token == access_token).first()
            )
            if user_token:
                creds_data = {
                    "token": user_token.token,
                    "refresh_token": user_token.refresh_token,
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "scopes": SCOPES
                    + ["https://www.googleapis.com/auth/gmail.readonly"],
                    "universe_domain": "googleapis.com",
                    "expiry": user_token.expiry,
                }
                self.creds = Credentials.from_authorized_user_info(
                    creds_data,
                    SCOPES + ["https://www.googleapis.com/auth/gmail.readonly"],
                )

                if not self.creds.valid:
                    if self.creds.expired and self.creds.refresh_token:
                        self.creds.refresh(GoogleRequest())
                        token_info = await self.save_credentials(db)
                        return token_info
                    else:
                        self.logger.error(
                            "Token is invalid and cannot be refreshed. Please reauthorize."
                        )
                        raise HTTPException(
                            status_code=401,
                            detail="Token is invalid and cannot be refreshed. Please reauthorize.",
                        )
            else:
                token_info = await self.save_credentials(db)
                return token_info
        except Exception as e:
            self.logger.error(f"Error loading credentials: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error loading credentials: {e}"
            )

    async def save_credentials(self, db: Session):
        """Save credentials to the database."""
        try:
            service = build("people", "v1", credentials=self.creds)
            profile = (
                service.people()
                .get(resourceName="people/me", personFields="names,emailAddresses")
                .execute()
            )
            name = profile["names"][0]["displayName"]
            id = profile["names"][0]["metadata"]["source"]["id"]
            self.email = profile["emailAddresses"][0]["value"]

            user = db.query(User).filter(User.email == self.email).first()
            if not user:
                user = User(id=str(id), name=name, email=self.email)
                db.add(user)

            user_token = (
                db.query(UserToken).filter(UserToken.email == self.email).first()
            )
            creds_json = json.loads(self.creds.to_json())

            if user_token:
                user_token.token = creds_json.get("token")
                user_token.refresh_token = creds_json.get("refresh_token")
                user_token.expiry = creds_json.get("expiry")
                user_token.updated_at = datetime.utcnow()
            else:
                user_token = UserToken(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    email=self.email,
                    token=creds_json.get("token"),
                    refresh_token=creds_json.get("refresh_token"),
                    expiry=creds_json.get("expiry"),
                )
                db.add(user_token)
            db.commit()
            db.refresh(user)
            db.refresh(user_token)
            return {
                "access_token": user_token.token,
                "refresh_token": user_token.refresh_token,
            }
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error saving credentials: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error saving credentials: {e}"
            )
