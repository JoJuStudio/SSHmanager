from .models import Config
from .bitwarden import list_connections


def load_config() -> Config:
    """Load connections directly from Bitwarden."""
    return Config(connections=list_connections())


def save_config(config: Config) -> None:
    """No-op. Local configuration storage is disabled."""
    return None
