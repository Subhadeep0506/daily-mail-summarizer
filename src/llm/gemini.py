import os

from .base import BaseLLM
from langchain_google_genai import ChatGoogleGenerativeAI


class GeminiLLM(BaseLLM):
    def __init__(self, model_name: str, temperature: float, **kwargs) -> None:
        self.model = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("GEMINI_API_KEY"),
            streaming=True if os.getenv("STREAMING_MODE") == "1" else False,
            **kwargs,
        )
        super().__init__()

    def get_model(self):
        return self.model
