from pydantic import BaseModel


class Summary(BaseModel):
    _id: str
    timestamp: str
    snippet: str
    file_id: str
