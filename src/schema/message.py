import datetime

from sqlalchemy import Column, DateTime, String, ARRAY
from sqlalchemy.dialects.postgresql import ENUM
from ..database.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, unique=True)
    message_id = Column(String, primary_key=True, nullable=False)
    thread_id = Column(String, nullable=False)
    labels = Column(ARRAY(String), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    subject = Column(String, nullable=True)
    add_from = Column(String, nullable=True)
    add_to = Column(String, nullable=True)
    snippet = Column(String, nullable=True)
    file_name = Column(String, nullable=False)
