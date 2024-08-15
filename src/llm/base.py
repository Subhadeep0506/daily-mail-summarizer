from abc import ABC, abstractmethod


class BaseLLMSummarizer:
    def __init__(self) -> None:
        self.model = None

    @abstractmethod
    def summarize_content(self, content):
        pass
