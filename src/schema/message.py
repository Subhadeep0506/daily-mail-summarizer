from pydantic import BaseModel


class Message(BaseModel):
    _id: str
    message_id: str
    thread_id: str
    label: str
    timestamp: str
    subject: str
    add_from: str
    add_to: str
    snippet: str
    file_id: str
