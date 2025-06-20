import json
import logging
import subprocess
from shutil import which
from typing import Any, Optional, List

from .models import Connection


def get_status() -> Optional[str]:
    """Return the Bitwarden CLI login status using ``bw status``.

    Returns ``"unlocked"`` when the vault is unlocked, ``"locked"`` when the
    CLI is logged in but the vault is locked, ``"unauthenticated"`` when not
    logged in, or ``None`` if the status could not be determined.
    """
    try:
        output = _run_bw(["status"])
        data = json.loads(output)
        return data.get("status")
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        logging.error("Failed to check Bitwarden status: %s", exc)
        return None


def is_unlocked() -> bool:
    """Return ``True`` if the Bitwarden vault is unlocked."""
    return get_status() == "unlocked"


def is_available() -> bool:
    """Return True if the Bitwarden CLI (`bw`) is available."""
    return which("bw") is not None


def _run_bw(args: list[str]) -> str:
    """Run ``bw`` with the given arguments and return stdout."""
    return subprocess.check_output(["bw", *args], text=True)


def _get_ssh_folder_id() -> Optional[str]:
    """Return the ID of the Bitwarden folder named ``SSH``."""
    try:
        output = _run_bw(["list", "folders"])
        folders = json.loads(output)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        logging.error("Failed to list Bitwarden folders: %s", exc)
        return None
    for folder in folders:
        if folder.get("name") == "SSH":
            return folder.get("id")
    return None


def fetch_credentials(item: str) -> Optional[dict[str, Any]]:
    """Fetch connection config from a Bitwarden item located in ``SSH`` folder.

    Parameters
    ----------
    item: str
        The Bitwarden item ID or name to fetch via `bw get item`.

    Returns
    -------
    Config dictionary parsed from the item's description, or ``None`` on
    failure.
    """
    if not is_available():
        logging.error("Bitwarden CLI not found in PATH")
        return None
    status = get_status()
    if status != "unlocked":
        if status == "locked":
            logging.error("Bitwarden vault is locked. Run 'bw unlock' first")
        elif status == "unauthenticated":
            logging.error("Bitwarden CLI not logged in. Run 'bw login' first")
        else:
            logging.error("Unable to determine Bitwarden login status")
        return None
    folder_id = _get_ssh_folder_id()
    if folder_id is None:
        logging.error("Bitwarden folder 'SSH' not found")
        return None
    try:
        output = _run_bw(["get", "item", item])
        data = json.loads(output)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        logging.error("Failed to fetch Bitwarden item: %s", exc)
        return None

    if data.get("folderId") != folder_id:
        logging.error("Item '%s' is not located in the 'SSH' folder", item)
        return None

    notes = data.get("notes") or data.get("notesPlain", "")
    if not notes:
        logging.error("Item '%s' has no description with config", item)
        return None
    try:
        cfg = json.loads(notes)
    except json.JSONDecodeError as exc:
        logging.error("Config in Bitwarden notes is invalid JSON: %s", exc)
        return None

    return cfg


def list_connections() -> List[Connection]:
    """Return all connections stored in the Bitwarden ``SSH`` folder.

    Only the item's login URI and username are used. Additional fields are
    ignored. Items missing these fields are skipped.
    """
    connections: List[Connection] = []
    if not (is_available() and is_unlocked()):
        return connections

    folder_id = _get_ssh_folder_id()
    if folder_id is None:
        logging.error("Bitwarden folder 'SSH' not found")
        return connections
    try:
        output = _run_bw(["list", "items", "--folderid", folder_id])
        items = json.loads(output)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        logging.error("Failed to list Bitwarden items: %s", exc)
        return connections

    for item in items:
        login = item.get("login", {})
        username = login.get("username")
        uris = login.get("uris") or []
        uri = uris[0].get("uri") if uris else None
        if not (username and uri):
            continue
        label = item.get("name") or username
        connections.append(Connection(label=label, host=uri, username=username))

    return connections
