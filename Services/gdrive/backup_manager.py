"""Google Drive backup/restore — persists SQLite DB + ChromaDB across HF Space rebuilds.

Flow:
  restore_from_drive()  → on startup  → pull latest snapshot from GDrive
  backup_to_drive()     → on shutdown → push snapshot to GDrive
  periodic_backup()     → every N min → push snapshot (background)

Env vars:
  GDRIVE_CREDENTIALS_BASE64 — base64-encoded service account JSON (set in HF Space secrets)
  GDRIVE_FOLDER_ID          — GDrive folder for backups
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from titan.config import settings

BACKUP_DIR_NAME = "titan_snapshot"
BACKUP_TAR_NAME = "titan_snapshot.tar.gz"

# Files/dirs to include in the snapshot
SNAPSHOT_PATHS = [
    "data/titan.db",
    "data/chroma/",
]


def _ensure_credentials() -> bool:
    """Write GDrive credentials from env var if file doesn't exist yet.

    On HF Space, the service account JSON is injected via
    GDRIVE_CREDENTIALS_BASE64 env var (set in Space secrets).
    """
    creds_path = Path(settings.GDRIVE_CREDENTIALS_FILE)
    if creds_path.exists():
        return True

    b64 = os.environ.get("GDRIVE_CREDENTIALS_BASE64", "")
    if not b64:
        return False

    try:
        creds_path.parent.mkdir(parents=True, exist_ok=True)
        decoded = base64.b64decode(b64)
        creds_path.write_bytes(decoded)
        return True
    except Exception:
        return False


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent  # Services/gdrive/ -> project root


def _create_snapshot() -> Optional[Path]:
    """Create a tar.gz snapshot of DB + ChromaDB. Returns path or None."""
    root = _get_project_root()
    tmp_dir = Path(tempfile.mkdtemp())
    snapshot_dir = tmp_dir / BACKUP_DIR_NAME
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    try:
        for path in SNAPSHOT_PATHS:
            src = root / path
            if src.is_file():
                (snapshot_dir / src.name).write_bytes(src.read_bytes())
            elif src.is_dir():
                dst = snapshot_dir / src.name
                shutil.copytree(src, dst, dirs_exist_ok=True)

        tar_path = tmp_dir / BACKUP_TAR_NAME
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(snapshot_dir, arcname=BACKUP_DIR_NAME)

        return tar_path
    except Exception as e:
        print(f"[backup] Snapshot creation failed: {e}", file=__import__("sys").stderr)
        return None
    finally:
        shutil.rmtree(snapshot_dir, ignore_errors=True)


def _extract_snapshot(tar_path: Path) -> bool:
    """Extract tar.gz into the project data directory."""
    root = _get_project_root()
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=root)
        # Move contents from titan_snapshot/ up one level
        extracted = root / BACKUP_DIR_NAME
        if extracted.is_dir():
            for item in extracted.iterdir():
                dest = root / "data" / item.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                if item.is_file():
                    item.replace(dest)
                elif item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                    shutil.rmtree(item, ignore_errors=True)
            shutil.rmtree(extracted, ignore_errors=True)
        return True
    except Exception as e:
        print(f"[backup] Snapshot extraction failed: {e}", file=__import__("sys").stderr)
        return False


def restore_from_drive() -> bool:
    """Download and restore the latest snapshot from Google Drive.

    Called on app startup. Silently no-ops if:
    - GDrive credentials aren't configured
    - No backup file exists in Drive yet
    """
    if not _ensure_credentials():
        return False

    try:
        from Services.gdrive.client import GoogleDriveClient

        client = GoogleDriveClient.get_instance()
        files = client.list_files(page_size=10)

        # Find the latest backup file
        backup_files = [f for f in files if f.get("name") == BACKUP_TAR_NAME]
        if not backup_files:
            print("[backup] No backup found in GDrive, skipping restore")
            return False

        # Sort by createdTime descending, take latest
        backup_files.sort(key=lambda f: f.get("createdTime", ""), reverse=True)
        latest = backup_files[0]
        file_id = latest["id"]

        local_path = f"/tmp/{BACKUP_TAR_NAME}"
        success = client.download_file(file_id, local_path)
        if not success:
            print("[backup] Download failed")
            return False

        result = _extract_snapshot(Path(local_path))
        if result:
            print(f"[backup] Restored from GDrive snapshot ({latest.get('createdTime', '?')})")
        return result
    except Exception as e:
        print(f"[backup] Restore error: {e}", file=__import__("sys").stderr)
        return False


def backup_to_drive() -> bool:
    """Create a snapshot and upload it to Google Drive.

    Called on app shutdown and periodically.
    """
    if not _ensure_credentials():
        return False

    try:
        from Services.gdrive.client import GoogleDriveClient

        tar_path = _create_snapshot()
        if tar_path is None:
            return False

        client = GoogleDriveClient.get_instance()
        result = client.upload_file(
            file_path=str(tar_path),
            mime_type="application/gzip",
            target_name=BACKUP_TAR_NAME,
        )
        os.unlink(tar_path)
        print(f"[backup] Uploaded backup to GDrive: {result.get('url', '?')}")
        return True
    except Exception as e:
        print(f"[backup] Upload error: {e}", file=__import__("sys").stderr)
        return False


def periodic_backup(interval_minutes: int = 15) -> None:
    """Run backup in a loop (intended for a background thread/async task)."""
    while True:
        time.sleep(interval_minutes * 60)
        try:
            backup_to_drive()
        except Exception:
            pass
