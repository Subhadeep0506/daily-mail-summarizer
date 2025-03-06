import os

from typing import Any
from infisical_client import (
    ClientSettings,
    InfisicalClient,
    ListSecretsOptions,
    AuthenticationOptions,
    UniversalAuthMethod,
)
from ...core.logger import SingletonLogger


class InfisicalManagedCredentials:
    def __init__(self) -> None:
        self.logger = SingletonLogger().logger
        self.client = InfisicalClient(
            ClientSettings(
                auth=AuthenticationOptions(
                    universal_auth=UniversalAuthMethod(
                        client_id=os.getenv("INFISICAL_CLIENT_ID"),
                        client_secret=os.getenv("INFISICAL_SECRET"),
                    ),
                ),
                cache_ttl=1,
            )
        )
        self()
        self.logger.info("Infisical Managed Credentials initialized")

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        try:
            _ = self.client.listSecrets(
                options=ListSecretsOptions(
                    environment="dev",
                    project_id=os.getenv("INFISICAL_PROJECT_ID"),
                    attach_to_process_env=True,
                ),
            )
            self.logger.info("Infisical Managed Credentials fetched")
        except Exception as e:
            self.logger.error(f"Error occured while fetching secrets: {e}")
