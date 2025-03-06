import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import ENUM
from ..database.database import Base


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(String, primary_key=True, unique=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    snippet = Column(String(100), nullable=False)
    file_id = Column(String(20), nullable=False)
