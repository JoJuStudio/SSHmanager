import json
import logging
import subprocess
from shutil import which
from typing import Any, Optional


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
