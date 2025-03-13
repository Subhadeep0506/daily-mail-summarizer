import datetime

from sqlalchemy import Column, DateTime, String, ARRAY
from sqlalchemy.dialects.postgresql import ENUM
from ..database.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, unique=True, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    file_url = Column(String, nullable=False)
