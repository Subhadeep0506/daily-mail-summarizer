import os
import base64
import uuid
from datetime import datetime
from typing import List, Optional
import json
from sqlalchemy.orm import Session
from fastapi import HTTPException
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.core.logger import SingletonLogger
from src.database.database import SessionLocal
from src.schema.user import UserToken, User
from src.models.token import UserToken as UserTokenModel
from src.models.user import User as UserModel


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

    async def load_credentials(self, db: Session, email: str):
        """Load credentials from the database or initiate OAuth flow."""
        self.email = email
        try:
            user_token = (
                db.query(UserToken).filter(UserToken.email == self.email).first()
            )
            if user_token:
                # Load existing credentials from database
                creds_data = {
                    "token": user_token.token,
                    "refresh_token": user_token.refresh_token,
                    "token_uri": user_token.token_uri,
                    "client_id": user_token.client_id,
                    "client_secret": user_token.client_secret,
                    "scopes": user_token.scopes.split(","),
                    "universe_domain": user_token.universe_domain,
                    "account": user_token.account,
                    "expiry": user_token.expiry,
                }
                self.creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

                if not self.creds.valid:
                    if self.creds.expired and self.creds.refresh_token:
                        self.creds.refresh(GoogleRequest())
                        user_info = await self.save_credentials(db)
                        return user_info
                    else:
                        self.logger.error(
                            "Token is invalid and cannot be refreshed. Please reauthorize."
                        )
                        raise HTTPException(
                            status_code=401,
                            detail="Token is invalid and cannot be refreshed. Please reauthorize.",
                        )
            else:
                self.logger.error(
                    "No valid credentials found for this user in the database. Please authorize the app."
                )
                raise HTTPException(
                    status_code=401,
                    detail="No valid credentials found. Please authorize the app.",
                )
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

            user = db.query(UserModel).filter(UserModel.email == self.email).first()
            if not user:
                user = UserModel(id=str(id), name=name, email=self.email)
                db.add(user)
                db.commit()
                db.refresh(user)

            user_token = (
                db.query(UserTokenModel).filter(UserTokenModel.email == self.email).first()
            )
            creds_json = json.loads(self.creds.to_json())

            if user_token:
                user_token.token = creds_json.get("token")
                user_token.refresh_token = creds_json.get("refresh_token")
                user_token.token_uri = creds_json.get("token_uri")
                user_token.client_id = creds_json.get("client_id")
                user_token.client_secret = creds_json.get("client_secret")
                user_token.scopes = ",".join(creds_json.get("scopes", []))
                user_token.universe_domain = creds_json.get("universe_domain")
                user_token.account = creds_json.get("account")
                user_token.expiry = creds_json.get("expiry")
                user_token.updated_at = datetime.utcnow()
            else:
                user_token = UserTokenModel(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    email=self.email,
                    token=creds_json.get("token"),
                    refresh_token=creds_json.get("refresh_token"),
                    token_uri=creds_json.get("token_uri"),
                    client_id=creds_json.get("client_id"),
                    client_secret=creds_json.get("client_secret"),
                    scopes=",".join(creds_json.get("scopes", [])),
                    universe_domain=creds_json.get("universe_domain"),
                    account=creds_json.get("account"),
                    expiry=creds_json.get("expiry"),
                    status=True,
                )
                db.add(user_token)
            db.commit()
            db.refresh(user_token)
            return user
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error saving credentials: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error saving credentials: {e}"
            )
