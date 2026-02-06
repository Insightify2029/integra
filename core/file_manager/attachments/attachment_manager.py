"""
Attachment Manager
==================
Hybrid document attachment system supporting DB BLOB, local files, and cloud links.

Features:
- Attach files to any entity (employees, companies, etc.)
- Multiple storage backends (BLOB, local, cloud)
- File versioning
- Checksum verification
"""

import os
import hashlib
import shutil
import mimetypes
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

from core.logging import app_logger


class StorageType(Enum):
    """File storage backend type."""
    DATABASE_BLOB = "blob"
    LOCAL_PATH = "local"
    CLOUD_LINK = "cloud"


@dataclass
class Attachment:
    """Represents a file attachment."""
    id: Optional[int]
    filename: str
    storage_type: StorageType
    storage_path: str
    file_size: int
    mime_type: str
    entity_type: str
    entity_id: int
    version: int = 1
    checksum: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None


class AttachmentManager:
    """Manages file attachments with hybrid storage."""

    def __init__(self, base_path: str = "attachments"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def attach_file(self, file_path: str, entity_type: str, entity_id: int,
                    storage_type: StorageType = StorageType.LOCAL_PATH,
                    user_id: int = None) -> Optional[Attachment]:
        """
        Attach a file to an entity.

        Args:
            file_path: Path to the source file
            entity_type: Entity type (e.g., 'employees', 'companies')
            entity_id: Entity ID
            storage_type: Where to store the file
            user_id: User performing the action

        Returns:
            Attachment object or None on failure
        """
        if not os.path.exists(file_path):
            app_logger.error(f"File not found: {file_path}")
            return None

        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        checksum = self._calculate_checksum(file_path)
        mime_type = self._get_mime_type(filename)

        if storage_type == StorageType.LOCAL_PATH:
            storage_path = self._store_local(file_path, entity_type, entity_id)
        elif storage_type == StorageType.DATABASE_BLOB:
            storage_path = self._store_blob(file_path, filename)
        else:
            storage_path = file_path

        attachment = Attachment(
            id=None,
            filename=filename,
            storage_type=storage_type,
            storage_path=storage_path,
            file_size=file_size,
            mime_type=mime_type,
            entity_type=entity_type,
            entity_id=entity_id,
            checksum=checksum,
            created_at=datetime.now(),
            created_by=user_id,
        )

        self._save_record(attachment)
        app_logger.info(f"Attached {filename} to {entity_type}/{entity_id}")
        return attachment

    def attach_from_cloud(self, cloud_link: str, entity_type: str,
                          entity_id: int,
                          filename: str = None) -> Optional[Attachment]:
        """
        Attach a cloud storage link.

        Args:
            cloud_link: Cloud file URL
            entity_type: Entity type
            entity_id: Entity ID
            filename: Display filename (extracted from URL if None)

        Returns:
            Attachment object
        """
        if not filename:
            filename = cloud_link.split("/")[-1].split("?")[0] or "cloud_file"

        attachment = Attachment(
            id=None,
            filename=filename,
            storage_type=StorageType.CLOUD_LINK,
            storage_path=cloud_link,
            file_size=0,
            mime_type=self._get_mime_type(filename),
            entity_type=entity_type,
            entity_id=entity_id,
            created_at=datetime.now(),
        )

        self._save_record(attachment)
        return attachment

    def get_attachments(self, entity_type: str,
                        entity_id: int) -> List[Attachment]:
        """
        Get all attachments for an entity.

        Args:
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            List of attachments
        """
        try:
            from core.database import select_all

            columns, rows = select_all("""
                SELECT * FROM attachments
                WHERE entity_type = %s AND entity_id = %s
                ORDER BY created_at DESC
            """, (entity_type, entity_id))

            return [self._row_to_attachment(row, columns) for row in rows]
        except Exception as e:
            app_logger.error(f"Failed to get attachments: {e}")
            return []

    def get_attachment_by_id(self, attachment_id: int) -> Optional[Attachment]:
        """Get a single attachment by ID."""
        try:
            from core.database import select_one

            result = select_one(
                "SELECT * FROM attachments WHERE id = %s",
                (attachment_id,)
            )
            if result:
                # Build column list from result
                return self._dict_to_attachment(result)
            return None
        except Exception as e:
            app_logger.error(f"Failed to get attachment: {e}")
            return None

    def get_file_content(self, attachment: Attachment) -> Optional[bytes]:
        """
        Read the actual file content.

        Args:
            attachment: Attachment object

        Returns:
            File content as bytes
        """
        if attachment.storage_type == StorageType.LOCAL_PATH:
            try:
                with open(attachment.storage_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                app_logger.error(f"Failed to read local file: {e}")
                return None

        elif attachment.storage_type == StorageType.DATABASE_BLOB:
            return self._load_blob(attachment.storage_path)

        elif attachment.storage_type == StorageType.CLOUD_LINK:
            app_logger.info("Cloud files must be downloaded separately")
            return None

        return None

    def create_new_version(self, attachment_id: int,
                           new_file_path: str,
                           user_id: int = None) -> Optional[Attachment]:
        """
        Create a new version of an existing attachment.

        Args:
            attachment_id: Original attachment ID
            new_file_path: Path to the new version file
            user_id: User creating the version

        Returns:
            New Attachment object
        """
        original = self.get_attachment_by_id(attachment_id)
        if not original:
            return None

        new_attachment = self.attach_file(
            new_file_path,
            original.entity_type,
            original.entity_id,
            original.storage_type,
            user_id,
        )

        if new_attachment:
            new_attachment.version = original.version + 1
            self._update_record(new_attachment)

        return new_attachment

    def get_versions(self, entity_type: str, entity_id: int,
                     filename: str) -> List[Attachment]:
        """Get all versions of a file."""
        try:
            from core.database import select_all

            columns, rows = select_all("""
                SELECT * FROM attachments
                WHERE entity_type = %s AND entity_id = %s AND filename = %s
                ORDER BY version DESC
            """, (entity_type, entity_id, filename))

            return [self._row_to_attachment(row, columns) for row in rows]
        except Exception as e:
            app_logger.error(f"Failed to get versions: {e}")
            return []

    def delete_attachment(self, attachment_id: int) -> bool:
        """Delete an attachment and its stored file."""
        attachment = self.get_attachment_by_id(attachment_id)
        if not attachment:
            return False

        # Delete physical file if local
        if attachment.storage_type == StorageType.LOCAL_PATH:
            try:
                os.remove(attachment.storage_path)
            except OSError:
                pass

        # Delete DB record
        try:
            from core.database import delete
            delete("DELETE FROM attachments WHERE id = %s", (attachment_id,))
            return True
        except Exception as e:
            app_logger.error(f"Failed to delete attachment: {e}")
            return False

    # ═══════════════════════════════════════════════════════
    # Internal Methods
    # ═══════════════════════════════════════════════════════

    def _store_local(self, file_path: str, entity_type: str,
                     entity_id: int) -> str:
        """Copy file to organized local storage."""
        dest_folder = os.path.join(self.base_path, entity_type, str(entity_id))
        os.makedirs(dest_folder, exist_ok=True)
        filename = os.path.basename(file_path)
        dest_path = os.path.join(dest_folder, filename)
        shutil.copy2(file_path, dest_path)
        return dest_path

    def _store_blob(self, file_path: str, filename: str) -> str:
        """Store file content in database as BLOB."""
        try:
            from core.database import insert_returning_id

            with open(file_path, 'rb') as f:
                content = f.read()

            blob_id = insert_returning_id("""
                INSERT INTO file_blobs (filename, content, created_at)
                VALUES (%s, %s, NOW())
            """, (filename, content))

            return f"blob://{blob_id}"
        except Exception as e:
            app_logger.error(f"Failed to store BLOB: {e}")
            return ""

    def _load_blob(self, storage_path: str) -> Optional[bytes]:
        """Load content from database BLOB."""
        if not storage_path.startswith("blob://"):
            return None

        blob_id = int(storage_path.replace("blob://", ""))

        try:
            from core.database import select_one
            result = select_one(
                "SELECT content FROM file_blobs WHERE id = %s",
                (blob_id,)
            )
            return result[0] if result else None
        except Exception as e:
            app_logger.error(f"Failed to load BLOB: {e}")
            return None

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _get_mime_type(self, filename: str) -> str:
        """Detect MIME type from filename."""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"

    def _save_record(self, attachment: Attachment):
        """Save attachment record to database."""
        try:
            from core.database import insert_returning_id

            attachment.id = insert_returning_id("""
                INSERT INTO attachments
                (filename, storage_type, storage_path, file_size, mime_type,
                 entity_type, entity_id, version, checksum, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                attachment.filename,
                attachment.storage_type.value,
                attachment.storage_path,
                attachment.file_size,
                attachment.mime_type,
                attachment.entity_type,
                attachment.entity_id,
                attachment.version,
                attachment.checksum,
                attachment.created_at,
                attachment.created_by,
            ))
        except Exception as e:
            app_logger.warning(f"Could not save attachment to DB: {e}")

    def _update_record(self, attachment: Attachment):
        """Update an attachment record."""
        try:
            from core.database import update
            update("""
                UPDATE attachments SET version = %s WHERE id = %s
            """, (attachment.version, attachment.id))
        except Exception as e:
            app_logger.warning(f"Could not update attachment record: {e}")

    def _row_to_attachment(self, row, columns) -> Attachment:
        """Convert a database row to Attachment."""
        data = dict(zip(columns, row)) if not isinstance(row, dict) else row
        return Attachment(
            id=data.get('id'),
            filename=data.get('filename', ''),
            storage_type=StorageType(data.get('storage_type', 'local')),
            storage_path=data.get('storage_path', ''),
            file_size=data.get('file_size', 0),
            mime_type=data.get('mime_type', ''),
            entity_type=data.get('entity_type', ''),
            entity_id=data.get('entity_id', 0),
            version=data.get('version', 1),
            checksum=data.get('checksum'),
            created_at=data.get('created_at'),
            created_by=data.get('created_by'),
        )

    def _dict_to_attachment(self, data) -> Attachment:
        """Convert dict or tuple result to Attachment."""
        if isinstance(data, dict):
            return self._row_to_attachment(data, list(data.keys()))
        return None
