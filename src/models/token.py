from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserToken(BaseModel):
    id: str
    user_id: str
    email: EmailStr
    token: str
    refresh_token: str
    token_uri: str
    client_id: str
    client_secret: str
    scopes: str
    universe_domain: str
    account: str
    expiry: str
    status: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True