from pydantic import BaseModel
from .types import types


class Message(BaseModel):
    _id: str
    message_id: str
    thread_id: str
    labels: str
    timestamp: str
    subject: str
    add_from: str
    add_to: str
    snippet: str
    file_name: str

    @staticmethod
    def get_schema():
        fileds = Message.__annotations__
        return [
            {"col_name": k, "type": types[str(v.__name__)]} for k, v in fileds.items()
        ]
