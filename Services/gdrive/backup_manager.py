"""Backup/restore — persists SQLite DB + ChromaDB across HF Space rebuilds.

Strategy:
  1. Try GDrive (Shared Drive supported via supportsAllDrives)
  2. Fallback to HF Space repo if GDrive fails (service account quota)

Flow:
  restore()  → on startup  → download & restore latest snapshot
  backup()   → on shutdown → create & upload snapshot
"""

from __future__ import annotations

import contextlib
import os
import shutil
import tarfile
import tempfile
import time
from pathlib import Path

from titan.config import settings

BACKUP_DIR_NAME = "titan_snapshot"
BACKUP_TAR_NAME = "titan_snapshot.tar.gz"
SNAPSHOT_PATHS = ["data/titan.db", "data/chroma/"]


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _get_hf_token() -> str:
    return os.environ.get("HF_TOKEN") or settings.HF_TOKEN or ""


def _create_snapshot() -> Path | None:
    """Create a tar.gz snapshot of DB + ChromaDB. Returns path or None."""
    root = _get_project_root()
    tmp_dir = Path(tempfile.mkdtemp())
    snapshot_dir = tmp_dir / BACKUP_DIR_NAME
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    try:
        for path in SNAPSHOT_PATHS:
            src = root / path
            if src.is_file() and src.exists():
                (snapshot_dir / src.name).write_bytes(src.read_bytes())
            elif src.is_dir() and src.exists():
                shutil.copytree(src, snapshot_dir / src.name, dirs_exist_ok=True)

        tar_path = tmp_dir / BACKUP_TAR_NAME
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(snapshot_dir, arcname=BACKUP_DIR_NAME)

        return tar_path
    except Exception as e:
        print(f"[backup] Snapshot failed: {e}", file=__import__("sys").stderr)
        return None
    finally:
        shutil.rmtree(snapshot_dir, ignore_errors=True)


def _extract_snapshot(tar_path: Path) -> bool:
    """Extract tar.gz into the project data directory."""
    root = _get_project_root()
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=root)
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
        print(f"[backup] Extraction failed: {e}", file=__import__("sys").stderr)
        return False


# ── GDrive (primary) ──────────────────────────────────────────────

GDRIVE_FOLDER_ID = "1GutEsjwj1I82B50usf-i-zH5zpVqONq6"
GDRIVE_FILE_NAME = BACKUP_TAR_NAME


def _upload_to_gdrive(tar_path: Path) -> bool:
    """Upload snapshot to Google Drive. Returns True on success."""
    creds_file = Path(settings.GDRIVE_CREDENTIALS_FILE)
    if not creds_file.exists():
        return False

    try:
        from Services.gdrive.client import GoogleDriveClient

        client = GoogleDriveClient.get_instance()
        # Override folder ID to the one shared with service account
        client._folder_id = GDRIVE_FOLDER_ID

        result = client.upload_file(
            file_path=str(tar_path),
            mime_type="application/gzip",
            target_name=GDRIVE_FILE_NAME,
        )
        print(f"[backup] Uploaded to GDrive: {result.get('url', '?')}")
        return True
    except Exception as e:
        err = str(e)
        if "storageQuotaExceeded" in err or "quota" in err.lower():
            print("[backup] GDrive quota exceeded, will fallback to HF repo")
        else:
            print(f"[backup] GDrive upload error: {e}", file=__import__("sys").stderr)
        return False


def _download_from_gdrive() -> bytes | None:
    """Download latest snapshot from Google Drive."""
    creds_file = Path(settings.GDRIVE_CREDENTIALS_FILE)
    if not creds_file.exists():
        return None

    try:
        from Services.gdrive.client import GoogleDriveClient

        client = GoogleDriveClient.get_instance()
        client._folder_id = GDRIVE_FOLDER_ID

        files = client.list_files(page_size=10)
        backup_files = [f for f in files if f.get("name") == GDRIVE_FILE_NAME]
        if not backup_files:
            return None

        # Sort by createdTime descending
        backup_files.sort(key=lambda f: f.get("createdTime", ""), reverse=True)
        latest = backup_files[0]

        local_path = f"/tmp/{BACKUP_TAR_NAME}"
        if not client.download_file(latest["id"], local_path):
            return None

        data = Path(local_path).read_bytes()
        Path(local_path).unlink(missing_ok=True)
        return data
    except Exception as e:
        print(f"[backup] GDrive download error: {e}", file=__import__("sys").stderr)
        return None


# ── HF Repo (fallback) ────────────────────────────────────────────

SPACE_ID = "Badjals/TitanAIO"
BACKUP_REPO_PATH = "backups/titan_snapshot.tar.gz"


def _upload_to_hf(data: bytes) -> bool:
    """Upload snapshot to HF Space repo."""
    token = _get_hf_token()
    if not token:
        return False

    try:
        from huggingface_hub import HfApi

        api = HfApi(token=token)
        api.upload_file(
            path_or_fileobj=data,
            path_in_repo=BACKUP_REPO_PATH,
            repo_id=SPACE_ID,
            repo_type="space",
            commit_message="chore: auto-backup data snapshot",
        )
        print("[backup] Uploaded to HF repo")
        return True
    except Exception as e:
        print(f"[backup] HF upload error: {e}", file=__import__("sys").stderr)
        return False


def _download_from_hf() -> bytes | None:
    """Download latest snapshot from HF Space repo."""
    token = _get_hf_token()
    if not token:
        return None

    try:
        from huggingface_hub import HfApi

        api = HfApi(token=token)
        path = api.hf_hub_download(
            repo_id=SPACE_ID,
            repo_type="space",
            filename=BACKUP_REPO_PATH,
        )
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        return None


# ── Public API ────────────────────────────────────────────────────


def restore() -> bool:
    """Restore data — tries GDrive first, then HF repo."""
    data = _download_from_gdrive()
    source = "GDrive"

    if data is None:
        data = _download_from_hf()
        source = "HF repo"

    if data is None:
        print("[backup] No backup found, skipping restore")
        return False

    tmp_path = Path(f"/tmp/{BACKUP_TAR_NAME}")
    try:
        tmp_path.write_bytes(data)
        result = _extract_snapshot(tmp_path)
        if result:
            print(f"[backup] Restored from {source}")
        return result
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def backup() -> bool:
    """Backup data — tries GDrive first, falls back to HF repo."""
    tar_path = _create_snapshot()
    if tar_path is None:
        return False

    try:
        data = tar_path.read_bytes()

        # Try GDrive first
        if _upload_to_gdrive(tar_path):
            return True

        # Fallback to HF repo
        print("[backup] Falling back to HF repo...")
        return _upload_to_hf(data)
    finally:
        tar_path.unlink(missing_ok=True)


def periodic_backup(interval_minutes: int = 15) -> None:
    """Run backup in a loop (background thread)."""
    while True:
        time.sleep(interval_minutes * 60)
        with contextlib.suppress(Exception):
            backup()
