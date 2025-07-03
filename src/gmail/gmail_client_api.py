import os
import base64
import uuid
from datetime import datetime
from typing import List, Optional
import json

from sqlalchemy.orm import Session
from fastapi import FastAPI, HTTPException, Query
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ..core.logger import SingletonLogger
from ..database.database import SessionLocal
from ..schema.user import UserToken, User

# Constants
REDIRECT_URI = "http://localhost:8009/oauth2callback"
SCOPES = [os.getenv("GMAIL_SCOPE", "https://www.googleapis.com/auth/gmail.readonly")]
CLIENT_SECRETS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


class GmailClient:
    def __init__(self):
        self.logger = SingletonLogger().logger
        self.email = None
        self.creds = None
        # self.REDIRECT_URI = os.getenv("APP_URL") + "/oauth2callback"

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
                        # Refresh the token
                        self.creds.refresh(GoogleRequest())
                        await self.save_credentials(db)
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
            # Ensure a User entry exists for the email
            user = db.query(User).filter(User.email == self.email).first()
            if not user:
                user = User(
                    id=str(uuid.uuid4()), name=self.email, email=self.email
                )  # Assuming name is email for simplicity
                db.add(user)
                db.commit()
                db.refresh(user)

            user_token = (
                db.query(UserToken).filter(UserToken.email == self.email).first()
            )

            token_info = self.creds.to_json()
            creds_json = json.loads(self.creds.to_json())

            if user_token:
                # Update existing token
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
                # Create new token
                user_token = UserToken(
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

    async def read_emails_for_date(self, email: str, start_date_str: str, end_date_str: str, db: Session):
        """Fetch emails within a date range."""
        try:
            await self.load_credentials(db, email)
            service = build("gmail", "v1", credentials=self.creds)
            results = service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])
            label_dict = {label["id"]: label["name"] for label in labels}
            start_datetime_str = f"{start_date_str}"
            end_datetime_str = f"{end_date_str}"
            start_datetime_obj = datetime.strptime(start_datetime_str, "%Y/%m/%d")
            end_datetime_obj = datetime.strptime(end_datetime_str, "%Y/%m/%d")
            start_timestamp = int(start_datetime_obj.timestamp())
            end_timestamp = int(end_datetime_obj.timestamp())
            query = f"after:{start_timestamp} before:{end_timestamp}"
            messages_result = (
                service.users().messages().list(userId="me", q=query).execute()
            )
            messages = messages_result.get("messages", [])

            if not messages:
                return {"message": "No messages found in the given date range."}

            fetched_messages = []
            for msg in messages:
                msg_id = msg["id"]
                msg_content = (
                    service.users().messages().get(userId="me", id=msg_id).execute()
                )
                msg_snippet = msg_content.get("snippet", "No snippet available")
                msg_payload = msg_content.get("payload", {})
                headers = msg_payload.get("headers", [])
                thread_id = msg_content.get("threadId", "No thread ID")
                subject = "No Subject"
                from_address = "No From address"
                to_address = "No To address"
                internal_date = int(msg_content.get("internalDate", 0)) / 1000
                date = datetime.fromtimestamp(internal_date).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                # Extract headers
                for header in headers:
                    if header["name"] == "Subject":
                        subject = header["value"]
                    elif header["name"] == "From":
                        from_address = header["value"]
                    elif header["name"] == "To":
                        to_address = header["value"]

                fetched_messages.append(
                    {
                        "id": str(uuid.uuid4()),
                        "message_id": msg_id,
                        "thread_id": thread_id,
                        "timestamp": date,
                        "labels": labels,
                        "subject": subject,
                        "add_from": from_address,
                        "add_to": to_address,
                        "snippet": msg_snippet,
                        "file_name": f"{msg_id}.txt",
                    }
                )
                self.save_message_to_file(
                    self.get_message_body(msg_payload), message_file_id=msg_id
                )
            return fetched_messages
        except HttpError as error:
            raise HTTPException(status_code=500, detail=f"An error occurred: {error}")

    def get_message_body(self, msg_payload):
        """Get the body of the message."""
        try:
            if "parts" in msg_payload:
                for part in msg_payload["parts"]:
                    if part["mimeType"] == "text/plain":
                        return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                            "utf-8"
                        )
                    elif part["mimeType"] == "text/html":
                        return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                            "utf-8"
                        )
            else:
                return base64.urlsafe_b64decode(msg_payload["body"]["data"]).decode(
                    "utf-8"
                )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error fetching message body: {e}"
            )

    def save_message_to_file(self, message_content: str, message_file_id: str):
        os.makedirs("temp", exist_ok=True)
        try:
            if message_content:
                with open(f"temp/{message_file_id}.txt", "w") as file:
                    file.write(message_content)
        except Exception as e:
            self.logger.error(f"An error occurred while saving message to file: {e}")
