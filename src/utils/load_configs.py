import yaml
from dotenv import load_dotenv


def load_env():
    try:
        config = {}
        with open("src/config/config.yaml", "r") as file:
            config = yaml.safe_load(file)
        loaded_env = load_dotenv()
        if loaded_env:
            return config
        else:
            raise ValueError(f"Could not load config.")
    except Exception as e:
        raise Exception(f"Error loading config: {e}")
