import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import ENUM
from ..database.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, unique=True)
    message_id = Column(String(50), nullable=False)
    thread_id = Column(String(50), nullable=False)
    labels = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    subject = Column(String(500), nullable=True)
    add_from = Column(String(100), nullable=True)
    add_to = Column(String(100), nullable=True)
    snippet = Column(String(1000), nullable=True)
    file_name = Column(String(20), nullable=False)
