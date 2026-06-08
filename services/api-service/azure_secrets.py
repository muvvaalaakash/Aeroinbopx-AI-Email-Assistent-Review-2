import os
from functools import lru_cache
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

@lru_cache(maxsize=128)
def get_secret(secret_name: str) -> str:
    """
    Retrieves secret from Azure Key Vault with LRU caching.
    Falls back to environment variables for local development.
    """
    # Try environment variable fallback first (e.g. google-client-id -> GOOGLE_CLIENT_ID)
    env_name = secret_name.upper().replace("-", "_")
    env_val = os.getenv(env_name)
    if env_val:
        return env_val

    vault_url = os.getenv("AZURE_KEYVAULT_URL")
    if vault_url:
        try:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)
            secret = client.get_secret(secret_name)
            return secret.value
        except Exception:
            pass

    return os.getenv(env_name, "")
