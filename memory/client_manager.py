"""
Client Manager — Multi-client support for Kiwi.

Each client has their own profile and memory stored at ~/.kiwi/clients/<name>/.
Active client tracked in ~/.kiwi/active_client.txt. Default client "self" is
created automatically and receives migrated data from legacy ~/.kiwi/profile.json
and ~/.kiwi/memory.json on first run.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

KIWI_DIR = Path.home() / ".kiwi"
CLIENTS_DIR = KIWI_DIR / "clients"
ACTIVE_CLIENT_FILE = KIWI_DIR / "active_client.txt"
LEGACY_PROFILE = KIWI_DIR / "profile.json"
LEGACY_MEMORY = KIWI_DIR / "memory.json"
LEGACY_ARCHIVE = KIWI_DIR / "episodic_archive.json"
DEFAULT_CLIENT = "self"

CLIENT_NAME_PATTERN = re.compile(r"^[a-z0-9_\-]{1,40}$")


def _normalize_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _validate_name(name: str) -> bool:
    return bool(CLIENT_NAME_PATTERN.match(name))


def ensure_setup() -> None:
    """First-run migration: create clients dir, move legacy files to 'self'."""
    KIWI_DIR.mkdir(parents=True, exist_ok=True)
    CLIENTS_DIR.mkdir(parents=True, exist_ok=True)

    self_dir = CLIENTS_DIR / DEFAULT_CLIENT
    self_dir.mkdir(parents=True, exist_ok=True)

    # Migrate legacy files if they exist and haven't been migrated yet
    legacy_profile_target = self_dir / "profile.json"
    if LEGACY_PROFILE.exists() and not legacy_profile_target.exists():
        shutil.copy2(LEGACY_PROFILE, legacy_profile_target)

    legacy_memory_target = self_dir / "memory.json"
    if LEGACY_MEMORY.exists() and not legacy_memory_target.exists():
        shutil.copy2(LEGACY_MEMORY, legacy_memory_target)

    legacy_archive_target = self_dir / "episodic_archive.json"
    if LEGACY_ARCHIVE.exists() and not legacy_archive_target.exists():
        shutil.copy2(LEGACY_ARCHIVE, legacy_archive_target)

    # Ensure active client file exists
    if not ACTIVE_CLIENT_FILE.exists():
        ACTIVE_CLIENT_FILE.write_text(DEFAULT_CLIENT)


def get_active_client() -> str:
    """Return the name of the currently active client."""
    ensure_setup()
    if ACTIVE_CLIENT_FILE.exists():
        name = ACTIVE_CLIENT_FILE.read_text().strip()
        if name and (CLIENTS_DIR / name).is_dir():
            return name
    return DEFAULT_CLIENT


def set_active_client(name: str) -> bool:
    """Switch to a different client. Returns False if client doesn't exist."""
    normalized = _normalize_name(name)
    if not _validate_name(normalized):
        return False
    if not (CLIENTS_DIR / normalized).is_dir():
        return False
    ACTIVE_CLIENT_FILE.write_text(normalized)
    return True


def create_client(name: str, description: str = "") -> tuple[bool, str]:
    """Create a new client directory. Returns (success, message)."""
    normalized = _normalize_name(name)
    if not _validate_name(normalized):
        return False, "Client name must be 1-40 chars, lowercase, alphanumeric/hyphens/underscores only"
    ensure_setup()
    client_dir = CLIENTS_DIR / normalized
    if client_dir.exists():
        return False, f"Client '{normalized}' already exists"
    client_dir.mkdir(parents=True, exist_ok=True)
    if description:
        (client_dir / "description.txt").write_text(description)
    return True, f"Created client '{normalized}'"


def delete_client(name: str) -> tuple[bool, str]:
    """Delete a client. Cannot delete the default 'self' client or the active one."""
    normalized = _normalize_name(name)
    if normalized == DEFAULT_CLIENT:
        return False, f"Cannot delete the default '{DEFAULT_CLIENT}' client"
    if normalized == get_active_client():
        return False, f"Cannot delete the active client. Switch first with /switch_client <name>"
    client_dir = CLIENTS_DIR / normalized
    if not client_dir.exists():
        return False, f"Client '{normalized}' does not exist"
    shutil.rmtree(client_dir)
    return True, f"Deleted client '{normalized}'"


def list_clients() -> list[dict]:
    """Return a list of all clients with metadata."""
    ensure_setup()
    active = get_active_client()
    clients = []
    for client_dir in sorted(CLIENTS_DIR.iterdir()):
        if not client_dir.is_dir():
            continue
        name = client_dir.name
        description = ""
        desc_file = client_dir / "description.txt"
        if desc_file.exists():
            description = desc_file.read_text().strip()
        clients.append({
            "name": name,
            "is_active": name == active,
            "description": description,
            "has_profile": (client_dir / "profile.json").exists(),
            "has_memory": (client_dir / "memory.json").exists(),
        })
    return clients


def get_client_dir(name: str | None = None) -> Path:
    """Get the directory for a specific client (or active if None)."""
    if name is None:
        name = get_active_client()
    ensure_setup()
    return CLIENTS_DIR / name


def profile_path(client: str | None = None) -> Path:
    return get_client_dir(client) / "profile.json"


def memory_path(client: str | None = None) -> Path:
    return get_client_dir(client) / "memory.json"


def archive_path(client: str | None = None) -> Path:
    return get_client_dir(client) / "episodic_archive.json"


def memory_md_path(client: str | None = None) -> Path:
    return get_client_dir(client) / "memory.md"
