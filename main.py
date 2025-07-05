from src.config.identity.infisical import InfisicalManagedCredentials
from src.utils import load_env, clean_temp

load_env()
inf_client = InfisicalManagedCredentials()
import os

from fastapi import FastAPI, HTTPException, Query, middleware
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.api.v1.auth.controller import router as auth_router
from src.api.v1.email.controller import router as email_router
from src.database.database import Base, engine

# Constants
REDIRECT_URI = "http://localhost:8089/oauth2callback"
SCOPES = [os.getenv("GMAIL_SCOPE", "https://www.googleapis.com/auth/gmail.readonly")]
CLIENT_SECRETS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


app = FastAPI(
    middleware=[
        middleware.Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )
    ]
)


# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)


app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(email_router, prefix="/email", tags=["email"])


@app.get("/")
async def index():
    return {"message": "Gmail Client Backend is running."}
