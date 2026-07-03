"""Backup/restore — persists SQLite DB + ChromaDB across HF Space rebuilds.

Stores snapshots directly in the HF Space repo (using HF_TOKEN).
No GDrive service account needed.

Flow:
  restore()  → on startup  → download latest snapshot from HF repo
  backup()   → on shutdown → commit snapshot to HF repo
"""

from __future__ import annotations

import os
import shutil
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Optional

from titan.config import settings

BACKUP_DIR_NAME = "titan_snapshot"
BACKUP_TAR_NAME = "titan_snapshot.tar.gz"
SNAPSHOT_PATHS = ["data/titan.db", "data/chroma/"]


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _get_hf_token() -> str:
    return os.environ.get("HF_TOKEN") or settings.HF_TOKEN or ""


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
            elif src.is_dir() and src.exists():
                dst = snapshot_dir / src.name
                shutil.copytree(src, dst, dirs_exist_ok=True)

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


# ── HF Repo Backup ────────────────────────────────────────────────

SPACE_ID = "Badjals/TitanAIO"
BACKUP_REPO_PATH = "backups/titan_snapshot.tar.gz"


def _upload_to_hf(data: bytes) -> bool:
    """Upload snapshot to HF Space repo using Hub API."""
    token = _get_hf_token()
    if not token:
        print("[backup] No HF_TOKEN set")
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
        print("[backup] Uploaded snapshot to HF repo")
        return True
    except Exception as e:
        print(f"[backup] HF upload error: {e}", file=__import__("sys").stderr)
        return False


def _download_from_hf() -> Optional[bytes]:
    """Download latest snapshot from HF Space repo."""
    token = _get_hf_token()
    if not token:
        return None

    try:
        from huggingface_hub import HfApi

        api = HfApi(token=token)
        data = api.hf_hub_download(
            repo_id=SPACE_ID,
            repo_type="space",
            filename=BACKUP_REPO_PATH,
        )
        with open(data, "rb") as f:
            return f.read()
    except Exception:
        return None


# ── Public API ────────────────────────────────────────────────────


def restore() -> bool:
    """Download and restore latest snapshot from HF Space repo.

    Called on app startup. Silently no-ops if no backup exists yet.
    """
    data = _download_from_hf()
    if data is None:
        print("[backup] No backup found in HF repo, skipping restore")
        return False

    tmp_path = Path(f"/tmp/{BACKUP_TAR_NAME}")
    try:
        tmp_path.write_bytes(data)
        result = _extract_snapshot(tmp_path)
        if result:
            print("[backup] Restored from HF repo")
        return result
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def backup() -> bool:
    """Create a snapshot and upload it to HF Space repo.

    Called on app shutdown and periodically.
    """
    tar_path = _create_snapshot()
    if tar_path is None:
        return False

    try:
        data = tar_path.read_bytes()
        result = _upload_to_hf(data)
        return result
    finally:
        tar_path.unlink(missing_ok=True)


def periodic_backup(interval_minutes: int = 15) -> None:
    """Run backup in a loop (background thread)."""
    while True:
        time.sleep(interval_minutes * 60)
        try:
            backup()
        except Exception:
            pass
