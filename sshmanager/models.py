from dataclasses import dataclass, asdict
from typing import List


@dataclass
class Connection:
    label: str
    host: str
    username: str
    port: int = 22
    folder: str = "Default"
    key_path: str | None = None
    initial_cmd: str | None = None


@dataclass
class Config:
    connections: List[Connection]

    def to_dict(self):
        return {"connections": [asdict(c) for c in self.connections]}

    @staticmethod
    def from_dict(data: dict) -> "Config":
        connections = [Connection(**c) for c in data.get("connections", [])]
        return Config(connections)
