import yaml
from dotenv import load_dotenv
from ..core.logger import SingletonLogger


def load_env():
    logger = SingletonLogger().logger
    try:
        config = {}
        with open("src/config/config.yaml", "r") as file:
            config = yaml.safe_load(file)
        loaded_env = load_dotenv()
        if loaded_env:
            logger.info("Environment variables loaded")
            return config
        else:
            logger.error("Could not load environment variables")
    except Exception as e:
        logger.error(f"Error loading env: {e}")
