import os

from typing import Any
from infisical_client import (
    ClientSettings,
    InfisicalClient,
    ListSecretsOptions,
    AuthenticationOptions,
    UniversalAuthMethod,
)


class InfisicalManagedCredentials:
    def __init__(self) -> None:
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

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        _ = self.client.listSecrets(
            options=ListSecretsOptions(
                environment="dev",
                project_id=os.getenv("INFISICAL_PROJECT_ID"),
                attach_to_process_env=True,
            ),
        )
