import os
import sys
import threading

import requests
from loguru import logger


def remote_sink(message):
    log_entry = message
    try:
        requests.post(os.getenv("LOG_URL"), data=str(log_entry))
    except Exception as e:
        # Optionally handle errors here
        pass


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
        logger.remove()
        logger.add("app.log", rotation="10 MB", colorize=True)
        logger.add(remote_sink)
        self.logger = logger
