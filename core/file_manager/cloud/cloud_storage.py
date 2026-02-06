"""
Cloud Storage
=============
Unified cloud storage integration for Google Drive, OneDrive, and Dropbox.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

from core.logging import app_logger


class CloudProvider(Enum):
    """Supported cloud storage providers."""
    GOOGLE_DRIVE = "google_drive"
    ONEDRIVE = "onedrive"
    DROPBOX = "dropbox"


@dataclass
class CloudFile:
    """Represents a file in cloud storage."""
    id: str
    name: str
    path: str
    size: int
    is_folder: bool
    shared_link: Optional[str] = None
    provider: Optional[CloudProvider] = None

    @property
    def size_formatted(self) -> str:
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        return f"{self.size / (1024 * 1024):.1f} MB"


class CloudStorageBase(ABC):
    """Abstract base for cloud storage providers."""

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the cloud provider."""
        pass

    @abstractmethod
    def list_files(self, folder_id: str = None) -> List[CloudFile]:
        """List files in a folder."""
        pass

    @abstractmethod
    def download(self, file_id: str, local_path: str) -> bool:
        """Download a file to local path."""
        pass

    @abstractmethod
    def upload(self, local_path: str, folder_id: str = None) -> Optional[CloudFile]:
        """Upload a local file to cloud."""
        pass

    @abstractmethod
    def get_shared_link(self, file_id: str) -> str:
        """Get a shared link for a file."""
        pass


class GoogleDriveStorage(CloudStorageBase):
    """Google Drive integration."""

    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path
        self.service = None
        self._authenticated = False

    def authenticate(self) -> bool:
        """Authenticate with Google Drive API."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from google_auth_oauthlib.flow import InstalledAppFlow

            SCOPES = ['https://www.googleapis.com/auth/drive']

            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            self.service = build('drive', 'v3', credentials=creds)
            self._authenticated = True
            return True
        except Exception as e:
            app_logger.error(f"Google Drive auth failed: {e}")
            return False

    def list_files(self, folder_id: str = None) -> List[CloudFile]:
        if not self.service:
            return []

        try:
            query = f"'{folder_id}' in parents" if folder_id else None
            results = self.service.files().list(
                q=query, pageSize=100,
                fields="files(id, name, size, mimeType)"
            ).execute()

            files = []
            for item in results.get('files', []):
                files.append(CloudFile(
                    id=item['id'],
                    name=item['name'],
                    path="",
                    size=int(item.get('size', 0)),
                    is_folder=item['mimeType'] == 'application/vnd.google-apps.folder',
                    provider=CloudProvider.GOOGLE_DRIVE,
                ))
            return files
        except Exception as e:
            app_logger.error(f"Google Drive list failed: {e}")
            return []

    def download(self, file_id: str, local_path: str) -> bool:
        if not self.service:
            return False

        try:
            from googleapiclient.http import MediaIoBaseDownload
            import io

            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(local_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                _, done = downloader.next_chunk()
            return True
        except Exception as e:
            app_logger.error(f"Google Drive download failed: {e}")
            return False

    def upload(self, local_path: str, folder_id: str = None) -> Optional[CloudFile]:
        if not self.service:
            return None

        try:
            from googleapiclient.http import MediaFileUpload
            from pathlib import Path

            file_metadata = {'name': Path(local_path).name}
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaFileUpload(local_path)
            file = self.service.files().create(
                body=file_metadata, media_body=media, fields='id,name,size'
            ).execute()

            return CloudFile(
                id=file['id'],
                name=file['name'],
                path="",
                size=int(file.get('size', 0)),
                is_folder=False,
                provider=CloudProvider.GOOGLE_DRIVE,
            )
        except Exception as e:
            app_logger.error(f"Google Drive upload failed: {e}")
            return None

    def get_shared_link(self, file_id: str) -> str:
        if not self.service:
            return ""

        try:
            self.service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()

            file = self.service.files().get(
                fileId=file_id, fields='webViewLink'
            ).execute()
            return file.get('webViewLink', '')
        except Exception as e:
            app_logger.error(f"Get shared link failed: {e}")
            return ""


class OneDriveStorage(CloudStorageBase):
    """OneDrive integration (placeholder for future implementation)."""

    def __init__(self, client_id: str = None):
        self.client_id = client_id
        self._authenticated = False

    def authenticate(self) -> bool:
        app_logger.info("OneDrive authentication - not yet implemented")
        return False

    def list_files(self, folder_id: str = None) -> List[CloudFile]:
        return []

    def download(self, file_id: str, local_path: str) -> bool:
        return False

    def upload(self, local_path: str, folder_id: str = None) -> Optional[CloudFile]:
        return None

    def get_shared_link(self, file_id: str) -> str:
        return ""


class DropboxStorage(CloudStorageBase):
    """Dropbox integration (placeholder for future implementation)."""

    def __init__(self, access_token: str = None):
        self.access_token = access_token
        self._authenticated = False

    def authenticate(self) -> bool:
        app_logger.info("Dropbox authentication - not yet implemented")
        return False

    def list_files(self, folder_id: str = None) -> List[CloudFile]:
        return []

    def download(self, file_id: str, local_path: str) -> bool:
        return False

    def upload(self, local_path: str, folder_id: str = None) -> Optional[CloudFile]:
        return None

    def get_shared_link(self, file_id: str) -> str:
        return ""


class CloudStorageManager:
    """Unified cloud storage manager."""

    def __init__(self):
        self.providers: Dict[CloudProvider, CloudStorageBase] = {}

    def add_provider(self, provider: CloudProvider, storage: CloudStorageBase):
        """Register a cloud storage provider."""
        self.providers[provider] = storage

    def authenticate_all(self) -> Dict[CloudProvider, bool]:
        """Authenticate all registered providers."""
        results = {}
        for provider, storage in self.providers.items():
            results[provider] = storage.authenticate()
        return results

    def list_files(self, provider: CloudProvider,
                   folder_id: str = None) -> List[CloudFile]:
        """List files from a specific provider."""
        storage = self.providers.get(provider)
        if not storage:
            return []
        return storage.list_files(folder_id)

    def download(self, provider: CloudProvider,
                 file_id: str, local_path: str) -> bool:
        """Download from a specific provider."""
        storage = self.providers.get(provider)
        if not storage:
            return False
        return storage.download(file_id, local_path)

    def upload(self, provider: CloudProvider,
               local_path: str, folder_id: str = None) -> Optional[CloudFile]:
        """Upload to a specific provider."""
        storage = self.providers.get(provider)
        if not storage:
            return None
        return storage.upload(local_path, folder_id)

    def download_from_link(self, link: str, local_path: str) -> bool:
        """
        Download a file from a cloud storage link.

        Auto-detects the provider from the URL.
        """
        if "drive.google.com" in link:
            provider = CloudProvider.GOOGLE_DRIVE
        elif "onedrive" in link or "sharepoint" in link:
            provider = CloudProvider.ONEDRIVE
        elif "dropbox.com" in link:
            provider = CloudProvider.DROPBOX
        else:
            return False

        storage = self.providers.get(provider)
        if not storage:
            return False

        file_id = self._extract_file_id(link, provider)
        if not file_id:
            return False

        return storage.download(file_id, local_path)

    def _extract_file_id(self, link: str, provider: CloudProvider) -> str:
        """Extract file ID from a cloud storage link."""
        import re

        if provider == CloudProvider.GOOGLE_DRIVE:
            # Extract ID from Google Drive URL
            match = re.search(r'/d/([a-zA-Z0-9_-]+)', link)
            if match:
                return match.group(1)
            match = re.search(r'id=([a-zA-Z0-9_-]+)', link)
            if match:
                return match.group(1)

        return ""
