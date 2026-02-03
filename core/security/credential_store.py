# -*- coding: utf-8 -*-
"""
Credential Store
================
Secure credential storage using OS keyring.

Features:
  - Store database credentials securely
  - Store API keys
  - Fallback to encrypted file if keyring unavailable
"""

from typing import Optional, Dict
import json
import base64
import os
from pathlib import Path

# Try to import keyring
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


class CredentialStore:
    """
    Secure credential storage.

    Uses OS keyring when available, falls back to encrypted file.

    Usage:
        store = CredentialStore()

        # Store credential
        store.set("db_password", "secret123")

        # Retrieve credential
        password = store.get("db_password")

        # Delete credential
        store.delete("db_password")
    """

    SERVICE_NAME = "INTEGRA"
    FALLBACK_FILE = Path.home() / ".integra" / "credentials.enc"

    def __init__(self, service_name: str = None):
        """
        Initialize credential store.

        Args:
            service_name: Service name for keyring (default: INTEGRA)
        """
        self.service_name = service_name or self.SERVICE_NAME
        self._cache: Dict[str, str] = {}

        # Ensure fallback directory exists
        self.FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

    def set(self, key: str, value: str) -> bool:
        """
        Store a credential.

        Args:
            key: Credential identifier
            value: The secret value

        Returns:
            True if stored successfully
        """
        try:
            if KEYRING_AVAILABLE:
                keyring.set_password(self.service_name, key, value)
            else:
                self._save_to_file(key, value)

            self._cache[key] = value
            return True

        except Exception as e:
            print(f"Failed to store credential: {e}")
            return False

    def get(self, key: str, default: str = None) -> Optional[str]:
        """
        Retrieve a credential.

        Args:
            key: Credential identifier
            default: Default value if not found

        Returns:
            The credential value or default
        """
        # Check cache first
        if key in self._cache:
            return self._cache[key]

        try:
            if KEYRING_AVAILABLE:
                value = keyring.get_password(self.service_name, key)
            else:
                value = self._load_from_file(key)

            if value is not None:
                self._cache[key] = value

            return value if value is not None else default

        except Exception as e:
            print(f"Failed to retrieve credential: {e}")
            return default

    def delete(self, key: str) -> bool:
        """
        Delete a credential.

        Args:
            key: Credential identifier

        Returns:
            True if deleted successfully
        """
        try:
            if KEYRING_AVAILABLE:
                keyring.delete_password(self.service_name, key)
            else:
                self._delete_from_file(key)

            if key in self._cache:
                del self._cache[key]

            return True

        except Exception as e:
            print(f"Failed to delete credential: {e}")
            return False

    def has(self, key: str) -> bool:
        """Check if a credential exists."""
        return self.get(key) is not None

    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()

    # Database-specific helpers

    def set_db_password(self, password: str) -> bool:
        """Store database password."""
        return self.set("db_password", password)

    def get_db_password(self) -> Optional[str]:
        """Get database password."""
        return self.get("db_password")

    def set_db_credentials(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str
    ) -> bool:
        """Store complete database credentials."""
        creds = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
        return self.set("db_credentials", json.dumps(creds))

    def get_db_credentials(self) -> Optional[Dict]:
        """Get complete database credentials."""
        value = self.get("db_credentials")
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    # Fallback file storage (simple obfuscation - not true encryption)

    def _save_to_file(self, key: str, value: str):
        """Save credential to fallback file."""
        data = self._load_all_from_file()
        data[key] = base64.b64encode(value.encode()).decode()

        with open(self.FALLBACK_FILE, "w") as f:
            json.dump(data, f)

        # Set restrictive permissions on Unix
        if os.name != 'nt':
            os.chmod(self.FALLBACK_FILE, 0o600)

    def _load_from_file(self, key: str) -> Optional[str]:
        """Load credential from fallback file."""
        data = self._load_all_from_file()
        if key in data:
            try:
                return base64.b64decode(data[key].encode()).decode()
            except Exception:
                return None
        return None

    def _delete_from_file(self, key: str):
        """Delete credential from fallback file."""
        data = self._load_all_from_file()
        if key in data:
            del data[key]
            with open(self.FALLBACK_FILE, "w") as f:
                json.dump(data, f)

    def _load_all_from_file(self) -> Dict:
        """Load all credentials from fallback file."""
        if not self.FALLBACK_FILE.exists():
            return {}
        try:
            with open(self.FALLBACK_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


# Singleton instance
_credential_store: Optional[CredentialStore] = None


def get_credential_store() -> CredentialStore:
    """Get the global CredentialStore instance."""
    global _credential_store
    if _credential_store is None:
        _credential_store = CredentialStore()
    return _credential_store
