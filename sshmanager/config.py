import json
from pathlib import Path
from .models import Config

CONFIG_PATH = Path.home() / ".sshmanager" / "connections.json"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return Config.from_dict(data)
    return Config(connections=[])


def save_config(config: Config) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(config.to_dict(), fh, indent=2)
