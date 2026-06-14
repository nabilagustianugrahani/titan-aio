"""Google Drive model storage — cache AI models in GDrive to avoid redownload."""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional

from Services.gdrive.client import GoogleDriveClient


class GDriveModelStore:
    """Model cache layer using Google Drive.

    FLUX, Wan 2.2, and other models are large (5-30GB).
    Downloading every session is wasteful. This caches them in GDrive.
    """

    MODELS = {
        "flux-schnell": {
            "huggingface_id": "black-forest-labs/FLUX.1-schnell",
            "gdrive_folder": "models/flux-schnell",
            "size_hint": "~12GB",
        },
        "flux-dev": {
            "huggingface_id": "black-forest-labs/FLUX.1-dev",
            "gdrive_folder": "models/flux-dev",
            "size_hint": "~23GB",
        },
        "wan-2-2": {
            "huggingface_id": "Wan-AI/Wan2.2-T2V-14B",
            "gdrive_folder": "models/wan-2-2",
            "size_hint": "~14GB",
        },
    }

    def __init__(self) -> None:
        self._gdrive = GoogleDriveClient.get_instance()
        self._cache_root = Path("/kaggle/working/model_cache")

    def get_cached_path(self, model_key: str) -> Optional[Path]:
        """Check if model is cached locally. Returns path or None."""
        cache_dir = self._cache_root / model_key
        if cache_dir.exists() and any(cache_dir.iterdir()):
            return cache_dir
        return None

    def download_from_gdrive(self, model_key: str) -> Optional[Path]:
        """Download model from GDrive to local cache."""
        model_info = self.MODELS.get(model_key)
        if not model_info:
            return None

        target = self._cache_root / model_key
        target.mkdir(parents=True, exist_ok=True)

        # List files in GDrive models folder
        parent_id = self._find_folder_id(model_info["gdrive_folder"])
        if not parent_id:
            print(f"[ModelStore] {model_info['gdrive_folder']} not found in GDrive")
            return None

        files = self._gdrive.list_files(folder_id=parent_id)
        if not files:
            print(f"[ModelStore] No files in {model_info['gdrive_folder']}")
            return None

        print(f"[ModelStore] Downloading {len(files)} files from GDrive...")
        for f in files:
            file_id = f.get("id")
            name = f.get("name")
            if file_id and name:
                local_path = target / name
                if not local_path.exists():
                    self._gdrive.download_file(file_id, str(local_path))
                    print(f"  Downloaded: {name}")

        return target if target.exists() else None

    def upload_to_gdrive(self, model_key: str, local_path: str) -> bool:
        """Upload cached model to GDrive for future sessions."""
        model_info = self.MODELS.get(model_key)
        if not model_info:
            return False

        folder_id = self._ensure_folder_path(model_info["gdrive_folder"])
        if not folder_id:
            return False

        path = Path(local_path)
        if path.is_dir():
            for f in path.iterdir():
                if f.is_file():
                    self._gdrive.upload_file(str(f), folder_id=folder_id)
                    print(f"  Uploaded: {f.name}")
        elif path.is_file():
            self._gdrive.upload_file(str(path), folder_id=folder_id)

        return True

    def ensure_model(self, model_key: str, hf_download_fn=None) -> Optional[Path]:
        """Get model — from local cache, GDrive, or download fresh.

        Priority:
        1. Local cache (/kaggle/working/model_cache/<key>)
        2. GDrive models folder
        3. Fresh download (huggingface)
        """
        # 1. Check local cache
        cached = self.get_cached_path(model_key)
        if cached:
            print(f"[ModelStore] Using local cache: {cached}")
            return cached

        # 2. Try GDrive
        print(f"[ModelStore] Not in local cache, checking GDrive...")
        from_gdrive = self.download_from_gdrive(model_key)
        if from_gdrive:
            return from_gdrive

        # 3. Download fresh
        print(f"[ModelStore] Downloading fresh model: {model_key}")
        if hf_download_fn:
            result = hf_download_fn()
            # Cache to GDrive for next time
            model_info = self.MODELS.get(model_key)
            if model_info and result:
                self.upload_to_gdrive(model_key, str(result))
            return result

        return None

    def _find_folder_id(self, path: str, create: bool = False) -> Optional[str]:
        """Find folder ID by path (e.g. 'models/flux-schnell')."""
        parts = path.split("/")
        current_id: Optional[str] = None

        for part in parts:
            if current_id is None:
                # Root level
                files = self._gdrive.list_files()
            else:
                files = self._gdrive.list_files(folder_id=current_id)

            found = None
            for f in files:
                if f.get("name") == part and f.get("mimeType") == "application/vnd.google-apps.folder":
                    found = f.get("id")
                    break

            if not found:
                if create:
                    result = self._gdrive.create_folder(part, parent_id=current_id)
                    found = result.get("folder_id")
                else:
                    return None
            current_id = found

        return current_id

    def _ensure_folder_path(self, path: str) -> Optional[str]:
        """Ensure folder path exists, creating if needed."""
        return self._find_folder_id(path, create=True)


async def ensure_model_from_gdrive(model_key: str) -> str | None:
    """Check GDrive for cached model. Returns path or None.
    Call this at the start of Kaggle notebooks to skip HF download if cached."""
    store = GDriveModelStore()
    path = store.ensure_model(model_key)
    if path:
        return str(path)
    return None


def upload_model_to_gdrive(model_key: str, local_path: str) -> bool:
    """Upload a model directory to GDrive for future sessions."""
    store = GDriveModelStore()
    return store.upload_to_gdrive(model_key, local_path)
