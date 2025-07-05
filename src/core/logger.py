import threading
from loguru import logger


class SingletonLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SingletonLogger, cls).__new__(
                        cls, *args, **kwargs
                    )
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        logger.add("app.log", rotation="10 MB")
        self.logger = logger
