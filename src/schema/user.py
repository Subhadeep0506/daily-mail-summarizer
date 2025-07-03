import datetime

from sqlalchemy import Column, DateTime, String, ARRAY, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import ENUM
from ..database.database import Base


class UserToken(Base):
    __tablename__ = "user_token"

    id = Column(String, unique=True, nullable=False, primary_key=True)
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    token_uri = Column(String, nullable=False)
    client_id = Column(String, nullable=False)
    client_secret = Column(String, nullable=False)
    scopes = Column(String, nullable=False)
    universe_domain = Column(String, nullable=False)
    account = Column(String, nullable=False)
    expiry = Column(String, nullable=False)
    status = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)


class User(Base):
    __tablename__ = "user"

    id = Column(String, unique=True, nullable=False, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
