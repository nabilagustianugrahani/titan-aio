"""Google Drive client for TITAN AIO — asset storage using service account."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from titan.config import settings

SCOPES = ["https://www.googleapis.com/auth/drive"]


class GoogleDriveClient:
    """Google Drive client using service account authentication."""

    _instance: GoogleDriveClient | None = None

    def __init__(
        self,
        credentials_file: str = "",
        folder_id: str = "",
    ) -> None:
        self._creds_file = credentials_file or settings.GDRIVE_CREDENTIALS_FILE
        self._folder_id = folder_id or settings.GDRIVE_FOLDER_ID
        self._service: Any = None

    @classmethod
    def get_instance(cls) -> GoogleDriveClient:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def service(self) -> Any:
        if self._service is None:
            creds = Credentials.from_service_account_file(
                self._creds_file, scopes=SCOPES,
            )
            self._service = build("drive", "v3", credentials=creds)
        return self._service

    def upload_file(
        self,
        file_path: str,
        mime_type: str = "image/png",
        target_name: str | None = None,
        folder_id: str | None = None,
    ) -> dict:
        """Upload a file to Google Drive."""
        folder = folder_id or self._folder_id
        name = target_name or Path(file_path).name

        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        file_metadata: dict[str, Any] = {"name": name}
        if folder:
            file_metadata["parents"] = [folder]

        file = (
            self.service.files()
            .create(body=file_metadata, media_body=media, fields="id,name,webViewLink")
            .execute()
        )
        return {
            "file_id": file.get("id"),
            "name": file.get("name"),
            "url": file.get("webViewLink"),
        }

    def list_files(self, folder_id: str | None = None, page_size: int = 20) -> list[dict]:
        """List files in a folder."""
        folder = folder_id or self._folder_id
        query = f"'{folder}' in parents and trashed=false" if folder else "trashed=false"

        results = (
            self.service.files()
            .list(q=query, pageSize=page_size, fields="files(id,name,mimeType,webViewLink,createdTime)")
            .execute()
        )
        return results.get("files", [])

    def create_folder(self, name: str, parent_id: str | None = None) -> dict:
        """Create a folder in Google Drive."""
        parent = parent_id or self._folder_id
        file_metadata: dict[str, Any] = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent:
            file_metadata["parents"] = [parent]

        folder = (
            self.service.files()
            .create(body=file_metadata, fields="id,name,webViewLink")
            .execute()
        )
        return {
            "folder_id": folder.get("id"),
            "name": folder.get("name"),
            "url": folder.get("webViewLink"),
        }

    def download_file(self, file_id: str, local_path: str) -> bool:
        """Download a file from Google Drive to local path."""
        try:
            request = self.service.files().get_media(fileId=file_id)
            from io import FileIO
            with FileIO(local_path, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            return True
        except Exception:
            return False

    def get_file(self, file_id: str) -> dict | None:
        """Get file metadata by ID."""
        try:
            return self.service.files().get(fileId=file_id, fields="id,name,mimeType,size,webViewLink").execute()
        except Exception:
            return None

    def delete_file(self, file_id: str) -> bool:
        """Delete a file by ID."""
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except Exception:
            return False
