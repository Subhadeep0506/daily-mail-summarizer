import logging
import threading


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
        self.logger = logging.getLogger("DailyMailSummarizer")
        self.logger.setLevel(logging.DEBUG)
        # FileHandler for file output
        file_handler = logging.FileHandler("app.log")
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
