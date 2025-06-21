"""Minimal Bitwarden CLI wrapper used by SSH Manager.

The application interacts with the `bw` command line tool instead of calling the
HTTP API directly. Only a few commands are required and this module abstracts
those operations.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
import shutil
import atexit
from typing import Any, List, Optional

from .models import Connection


_DEFAULT_SERVER = "https://vault.bitwarden.com"
_session: Optional[str] = None
_server: str = _DEFAULT_SERVER
_last_error: Optional[str] = None
_config_dir: Optional[str] = None


def _cleanup() -> None:
    """Remove the temporary Bitwarden config directory on exit."""
    if _config_dir:
        shutil.rmtree(_config_dir, ignore_errors=True)


atexit.register(_cleanup)


def _run_bw(args: List[str], parse_json: bool = True) -> Any:
    """Run a Bitwarden CLI command and return the parsed output."""
    env = os.environ.copy()
    if _server:
        env["BW_SERVER"] = _server
    if _session:
        env["BW_SESSION"] = _session
    if _config_dir:
        env["BW_CONFIGDIR"] = _config_dir
    try:
        result = subprocess.run(
            ["bw", *args],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        logging.error("bw CLI not found")
        return None
    except subprocess.CalledProcessError as exc:
        logging.error("bw command failed: %s", exc.stderr.strip())
        return None
    output = result.stdout.strip()
    if parse_json:
        try:
            return json.loads(output) if output else None
        except json.JSONDecodeError as exc:
            logging.error("Failed to parse bw output: %s", exc)
            return None
    return output


def login(
    email: str,
    password: str,
    server: str | None = None,
    device_name: str | None = None,
    device_identifier: str | None = None,
) -> bool:
    """Authenticate using the Bitwarden CLI."""

    global _session, _server, _last_error, _config_dir
    _last_error = None
    _session = None

    # Use a temporary config directory so the user's bw CLI state is untouched
    if _config_dir:
        shutil.rmtree(_config_dir, ignore_errors=True)
    _config_dir = tempfile.mkdtemp(prefix="sshmanager_bw_")

    if not email or not password:
        _last_error = "Email and password are required"
        return False

    _server = server or _DEFAULT_SERVER
    env = os.environ.copy()
    env["BW_SERVER"] = _server
    env["BW_CONFIGDIR"] = _config_dir
    try:
        result = subprocess.run(
            ["bw", "login", email, password, "--raw"],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        _session = result.stdout.strip()
    except FileNotFoundError:
        _last_error = "bw CLI not found"
        logging.error(_last_error)
        return False
    except subprocess.CalledProcessError as exc:
        _last_error = exc.stderr.strip() or "Bitwarden login failed"
        logging.error("bw login failed: %s", _last_error)
        return False

    # Initial sync to ensure items are available
    _run_bw(["sync"], parse_json=False)
    return True


def get_status() -> str:
    """Return ``"unlocked"`` if a session is available."""

    return "unlocked" if _session else "unauthenticated"


def is_unlocked() -> bool:
    return _session is not None


def get_last_error() -> Optional[str]:
    return _last_error


def _get_ssh_folder_id() -> Optional[str]:
    data = _run_bw(["list", "folders"])
    if not data:
        return None
    for folder in data:
        if folder.get("name") == "SSH":
            return folder.get("id")
    return None


def fetch_credentials(item: str) -> Optional[dict[str, Any]]:
    """Fetch connection configuration from a Bitwarden item."""
    if not is_unlocked():
        return None
    data = _run_bw(["get", "item", item])
    if not data:
        return None
    notes = data.get("notes") or data.get("notesPlain", "")
    if not notes:
        return None
    try:
        return json.loads(notes)
    except json.JSONDecodeError as exc:
        logging.error("Config in Bitwarden notes is invalid JSON: %s", exc)
        return None


def list_connections() -> List[Connection]:
    """Return all connections stored in the ``SSH`` folder."""
    conns: List[Connection] = []
    if not is_unlocked():
        return conns
    folder_id = _get_ssh_folder_id()
    if folder_id is None:
        logging.error("Bitwarden folder 'SSH' not found")
        return conns
    data = _run_bw(["list", "items", "--folderid", folder_id])
    if not data:
        return conns
    for item in data:
        login_data = item.get("login", {})
        username = login_data.get("username")
        uris = login_data.get("uris") or []
        uri = uris[0].get("uri") if uris else None
        if not (username and uri):
            continue
        label = item.get("name") or username
        conns.append(Connection(label=label, host=uri, username=username))
    return conns


def sync() -> Any:
    """Perform a Bitwarden sync using the CLI."""
    if not is_unlocked():
        return None
    return _run_bw(["sync"])
