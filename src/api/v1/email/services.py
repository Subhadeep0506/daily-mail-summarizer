import base64
import json
import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from src.api.v1.auth.services import GoogleOAuth2Service
from src.core.logger import SingletonLogger
from src.database.database import SessionLocal
from src.schema.user import User, UserToken

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]


class GmailService:
    """Handles email fetching and related operations."""

    def __init__(self, auth: GoogleOAuth2Service):
        self.auth = auth
        self.logger = SingletonLogger().logger

    async def read_emails_for_date(
        self, access_token: str, start_date_str: str, end_date_str: str, db: Session
    ):
        """Fetch emails within a date range."""
        try:
            _ = await self.auth.load_credentials(access_token, db)
            service = build("gmail", "v1", credentials=self.auth.creds)
            results = service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])
            label_dict = {label["id"]: label["name"] for label in labels}

            start_datetime_obj = datetime.strptime(start_date_str, "%Y/%m/%d")
            end_datetime_obj = datetime.strptime(end_date_str, "%Y/%m/%d")
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
