from abc import ABC, abstractmethod


class BaseLLM(ABC):
    def __init__(self) -> None:
        self.model = None

    @abstractmethod
    def get_model(self):
        pass


class BaseEmbeddings(ABC):
    def __init__(self) -> None:
        self.model = None

    @abstractmethod
    def get_model(self):
        pass
