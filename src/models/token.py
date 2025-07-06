from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserToken(BaseModel):
    id: str
    user_id: str
    email: EmailStr
    token: str
    refresh_token: str
    expiry: str
    status: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
