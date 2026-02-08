"""
Credential Store
================
Secure storage for credentials using OS keyring with file fallback.

Features:
- OS keyring integration (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- Encrypted file fallback when keyring is unavailable
- Thread-safe access
- Audit logging of credential operations

Usage:
    from core.security.credential_store import get_credential_store

    store = get_credential_store()

    # Store database credentials
    store.set_credential("db_password", "my_secret_password")

    # Retrieve credentials
    password = store.get_credential("db_password")

    # Delete credentials
    store.delete_credential("db_password")

    # Store structured credentials
    store.set_credentials("database", {
        "host": "localhost",
        "port": "5432",
        "password": "secret"
    })

    # Retrieve structured credentials
    db_creds = store.get_credentials("database")
"""

import json
import os
import threading
from pathlib import Path
from typing import Optional, Dict, Any

from core.logging import app_logger

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


# ============================================================
# Constants
# ============================================================

SERVICE_NAME = "INTEGRA"
CREDENTIAL_FILE = Path(__file__).parent.parent.parent / ".credentials.enc"
CREDENTIAL_KEY_FILE = Path(__file__).parent.parent.parent / ".credential_key"


# ============================================================
# Credential Store
# ============================================================

class CredentialStore:
    """
    Secure credential storage with keyring and encrypted file fallback.

    Thread-safe singleton pattern.
    """

    _instance: Optional['CredentialStore'] = None
    _cls_lock = threading.Lock()

    def __new__(cls) -> 'CredentialStore':
        """Thread-safe singleton."""
        if cls._instance is None:
            with cls._cls_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._lock = threading.Lock()
        self._use_keyring = KEYRING_AVAILABLE
        self._fernet: Optional[Any] = None

        # Test keyring availability
        if self._use_keyring:
            self._use_keyring = self._test_keyring()

        # Initialize file-based fallback if needed
        if not self._use_keyring and CRYPTOGRAPHY_AVAILABLE:
            self._init_file_store()

        backend = "keyring" if self._use_keyring else "encrypted_file"
        app_logger.info(f"CredentialStore initialized (backend: {backend})")

    def _test_keyring(self) -> bool:
        """Test if keyring is actually functional."""
        try:
            test_key = f"{SERVICE_NAME}_test"
            keyring.set_password(SERVICE_NAME, test_key, "test")
            result = keyring.get_password(SERVICE_NAME, test_key)
            keyring.delete_password(SERVICE_NAME, test_key)
            return result == "test"
        except Exception as e:
            app_logger.warning(f"Keyring not functional, using file fallback: {e}")
            return False

    def _init_file_store(self) -> None:
        """Initialize encrypted file store."""
        try:
            if CREDENTIAL_KEY_FILE.exists():
                self._fernet = Fernet(CREDENTIAL_KEY_FILE.read_bytes())
            else:
                key = Fernet.generate_key()
                CREDENTIAL_KEY_FILE.write_bytes(key)
                try:
                    os.chmod(CREDENTIAL_KEY_FILE, 0o600)
                except OSError as e:
                    app_logger.warning(f"Could not set key file permissions: {e}")
                self._fernet = Fernet(key)

            # Create empty credential file if it doesn't exist
            if not CREDENTIAL_FILE.exists():
                self._write_file_store({})

        except Exception as e:
            app_logger.error(f"Failed to initialize file credential store: {e}")

    def _read_file_store(self) -> Dict[str, str]:
        """Read credentials from encrypted file."""
        if not CREDENTIAL_FILE.exists() or not self._fernet:
            return {}

        try:
            encrypted = CREDENTIAL_FILE.read_bytes()
            decrypted = self._fernet.decrypt(encrypted)
            return json.loads(decrypted.decode('utf-8'))
        except (InvalidToken, json.JSONDecodeError, OSError) as e:
            app_logger.error(f"Failed to read credential file: {e}")
            return {}

    def _write_file_store(self, data: Dict[str, str]) -> bool:
        """Write credentials to encrypted file."""
        if not self._fernet:
            return False

        try:
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            encrypted = self._fernet.encrypt(json_data)
            CREDENTIAL_FILE.write_bytes(encrypted)
            try:
                os.chmod(CREDENTIAL_FILE, 0o600)
            except OSError:
                pass
            return True
        except (OSError, TypeError) as e:
            app_logger.error(f"Failed to write credential file: {e}")
            return False

    # ============================================================
    # Public API
    # ============================================================

    def set_credential(self, key: str, value: str) -> bool:
        """
        Store a credential securely.

        Args:
            key: Credential identifier (e.g., "db_password")
            value: Credential value

        Returns:
            True if stored successfully
        """
        with self._lock:
            try:
                if self._use_keyring:
                    keyring.set_password(SERVICE_NAME, key, value)
                    app_logger.debug(f"Credential '{key}' stored in keyring")
                    return True
                else:
                    store = self._read_file_store()
                    store[key] = value
                    success = self._write_file_store(store)
                    if success:
                        app_logger.debug(f"Credential '{key}' stored in file")
                    return success
            except Exception as e:
                app_logger.error(f"Failed to store credential '{key}': {e}")
                return False

    def get_credential(self, key: str) -> Optional[str]:
        """
        Retrieve a credential.

        Args:
            key: Credential identifier

        Returns:
            Credential value or None if not found
        """
        with self._lock:
            try:
                if self._use_keyring:
                    value = keyring.get_password(SERVICE_NAME, key)
                    return value
                else:
                    store = self._read_file_store()
                    return store.get(key)
            except Exception as e:
                app_logger.error(f"Failed to retrieve credential '{key}': {e}")
                return None

    def delete_credential(self, key: str) -> bool:
        """
        Delete a credential.

        Args:
            key: Credential identifier

        Returns:
            True if deleted successfully
        """
        with self._lock:
            try:
                if self._use_keyring:
                    keyring.delete_password(SERVICE_NAME, key)
                    app_logger.debug(f"Credential '{key}' deleted from keyring")
                    return True
                else:
                    store = self._read_file_store()
                    if key in store:
                        del store[key]
                        success = self._write_file_store(store)
                        if success:
                            app_logger.debug(f"Credential '{key}' deleted from file")
                        return success
                    return False
            except Exception as e:
                app_logger.error(f"Failed to delete credential '{key}': {e}")
                return False

    def has_credential(self, key: str) -> bool:
        """
        Check if a credential exists.

        Args:
            key: Credential identifier

        Returns:
            True if credential exists
        """
        return self.get_credential(key) is not None

    def set_credentials(self, namespace: str, credentials: Dict[str, str]) -> bool:
        """
        Store multiple credentials under a namespace.

        Args:
            namespace: Namespace (e.g., "database", "email")
            credentials: Dict of key-value pairs

        Returns:
            True if all stored successfully
        """
        try:
            json_value = json.dumps(credentials, ensure_ascii=False)
            return self.set_credential(f"{namespace}_bundle", json_value)
        except (TypeError, ValueError) as e:
            app_logger.error(f"Failed to serialize credentials for '{namespace}': {e}")
            return False

    def get_credentials(self, namespace: str) -> Optional[Dict[str, str]]:
        """
        Retrieve multiple credentials from a namespace.

        Args:
            namespace: Namespace

        Returns:
            Dict of credentials or None
        """
        try:
            json_value = self.get_credential(f"{namespace}_bundle")
            if json_value:
                return json.loads(json_value)
            return None
        except json.JSONDecodeError as e:
            app_logger.error(f"Failed to parse credentials for '{namespace}': {e}")
            return None

    def list_keys(self) -> list:
        """
        List all credential keys (file backend only).

        Returns:
            List of credential keys
        """
        with self._lock:
            if not self._use_keyring:
                store = self._read_file_store()
                return list(store.keys())
            else:
                app_logger.debug("list_keys not supported with keyring backend")
                return []

    @property
    def backend(self) -> str:
        """Get the current storage backend name."""
        if self._use_keyring:
            return "keyring"
        elif self._fernet:
            return "encrypted_file"
        else:
            return "none"


# ============================================================
# Singleton Access
# ============================================================

_credential_store: Optional[CredentialStore] = None
_store_lock = threading.Lock()


def get_credential_store() -> CredentialStore:
    """
    Get the CredentialStore singleton (thread-safe).

    Returns:
        CredentialStore instance
    """
    global _credential_store
    if _credential_store is None:
        with _store_lock:
            if _credential_store is None:
                _credential_store = CredentialStore()
    return _credential_store
