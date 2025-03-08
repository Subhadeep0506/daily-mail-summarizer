import os

from .base import BaseLLM
from langchain_cohere import ChatCohere


class CohereLLM(BaseLLM):
    def __init__(self, model_name: str, temperature: float) -> None:
        self.model = ChatCohere(
            model=model_name,
            temperature=temperature,
            cohere_api_key=os.getenv("COHERE_API_KEY"),
            streaming=True if os.getenv("STREAMING_MODE") == "1" else False,
        )
        super().__init__()

    def get_model(self):
        return self.model
