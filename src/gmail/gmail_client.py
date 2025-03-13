import os.path
import base64
import uuid

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from ..core.logger import SingletonLogger


class GmailClient:
    def __init__(self, email="subhadeepdoublecap@gmail.com") -> None:
        self.logger = SingletonLogger().logger
        self.creds = None
        try:
            if os.getenv("DEBUG_MODE") == "0":
                if os.path.exists("token.json"):
                    self.logger.info("Loading Gmail client from token.json")
                    self.creds = Credentials.from_authorized_user_file(
                        "token.json", [os.getenv("GMAIL_SCOPE")]
                    )
                if not self.creds or not self.creds.valid:
                    self.logger.info(
                        "Token Expired. Refreshing Gmail client from credentials.json"
                    )
                    if self.creds and self.creds.expired and self.creds.refresh_token:
                        self.creds.refresh(Request())
                    else:
                        self.logger.info(
                            "Creating new Gmail client from credentials.json"
                        )
                        flow = InstalledAppFlow.from_client_secrets_file(
                            "credentials.json",
                            [os.getenv("GMAIL_SCOPE")],
                            redirect_uri="urn:ietf:wg:oauth:2.0:oob",
                        )
                        auth_url, _ = flow.authorization_url(prompt="consent")
                        print("Please go to this URL: {}".format(auth_url))
                        code = input("Enter the authorization code: ")
                        flow.fetch_token(code=code)
                        print("Creds:", flow.credentials.to_json())
                        self.creds = flow.credentials
                    # Save the credentials for the next run
                    with open("token.json", "w") as token:
                        token.write(self.creds.to_json())
            else:
                if os.path.exists("token.json"):
                    self.creds = Credentials.from_authorized_user_file(
                        "token.json", [os.getenv("GMAIL_SCOPE")]
                    )
                if not self.creds or not self.creds.valid:
                    if self.creds and self.creds.expired and self.creds.refresh_token:
                        self.creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            "credentials.json", [os.getenv("GMAIL_SCOPE")]
                        )
                        self.creds = flow.run_local_server(
                            bind_addr="0.0.0.0",
                            open_browser=True,
                            port=8088,
                        )
                    # Save the credentials for the next run
                    with open("token.json", "w") as token:
                        token.write(self.creds.to_json())
        except Exception as e:
            self.logger.error(f"An error occured while loading Gmail client: {e}")

    def read_emails_for_date(self, start_date_str: str, end_date_str: str):
        """Shows basic usage of the Gmail API.
        Lists the user's Gmail labels and messages.
        """
        try:
            self.logger.info(
                f"Reading emails from Gmail. Start Date: {start_date_str}, End Date: {end_date_str}"
            )
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
                self.logger.error("No messages found")
                return []

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
                label_ids = msg_content.get("labelIds", [])
                labels = [
                    label_dict.get(label_id, "Unknown label") for label_id in label_ids
                ]
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
                        "message_content": self.get_message_body(msg_payload),
                    }
                )
            self.logger.info(
                f"Emails read from Gmail. Total emails: {len(fetched_messages)}"
            )
            return fetched_messages
        except HttpError as error:
            self.logger.error(f"An error occurred while fetching messages: {error}")
            return []

    def get_message_body(self, msg_payload) -> str:
        """Get the body of the message"""
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
                        return "Meessage is empty."
            else:
                return base64.urlsafe_b64decode(msg_payload["body"]["data"]).decode(
                    "utf-8"
                )
        except Exception as e:
            self.logger.error(f"An error occurred while fetching message body: {e}")
            return "Message not parsed."
