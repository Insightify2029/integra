"""
Authentication Manager
======================
Handles user authentication with Argon2 password hashing and account lockout.

Features:
- Argon2id password hashing (memory-hard, side-channel resistant)
- Account lockout after failed attempts
- Session management with timeout
- Audit logging of all auth events

Usage:
    from core.security.auth_manager import get_auth_manager

    auth = get_auth_manager()

    # Register/hash password
    hashed = auth.hash_password("my_secure_password")

    # Verify password
    if auth.verify_password("my_secure_password", hashed):
        print("Password correct!")

    # Login with lockout protection
    success, message = auth.authenticate(user_id=1, password="pass123")
    if success:
        print("Authenticated!")
    else:
        print(f"Failed: {message}")

    # Check lockout status
    if auth.is_locked_out(user_id=1):
        remaining = auth.get_lockout_remaining(user_id=1)
        print(f"Locked out for {remaining} seconds")
"""

import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from dataclasses import dataclass, field

from core.logging import app_logger, audit_logger

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import (
        VerifyMismatchError,
        VerificationError,
        InvalidHashError,
    )
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False
    PasswordHasher = None

import hmac
import hashlib


# ============================================================
# Configuration
# ============================================================

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
SESSION_TIMEOUT_MINUTES = 480  # 8 hours
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # 64 MB
ARGON2_PARALLELISM = 4


# ============================================================
# Data Classes
# ============================================================

@dataclass
class LoginAttempt:
    """Tracks login attempts for a user."""
    user_id: int
    failed_count: int = 0
    last_failed: Optional[datetime] = None
    locked_until: Optional[datetime] = None


@dataclass
class UserSession:
    """Represents an active user session."""
    user_id: int
    user_name: str
    role: str
    login_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True


# ============================================================
# Authentication Manager
# ============================================================

class AuthManager:
    """
    Manages authentication, password hashing, and account lockout.

    Thread-safe singleton pattern.
    """

    _instance: Optional['AuthManager'] = None
    _cls_lock = threading.Lock()

    def __new__(cls) -> 'AuthManager':
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

        # Password hasher
        if ARGON2_AVAILABLE:
            self._hasher = PasswordHasher(
                time_cost=ARGON2_TIME_COST,
                memory_cost=ARGON2_MEMORY_COST,
                parallelism=ARGON2_PARALLELISM,
            )
        else:
            self._hasher = None
            app_logger.warning(
                "argon2-cffi not available. Using PBKDF2 fallback. "
                "Install argon2-cffi for stronger password hashing."
            )

        # Login attempts tracking
        self._login_attempts: Dict[int, LoginAttempt] = {}

        # Active session
        self._session: Optional[UserSession] = None

        # Password verification callback (for DB lookup)
        self._password_lookup = None

        app_logger.info("AuthManager initialized")

    # ============================================================
    # Password Hashing
    # ============================================================

    def hash_password(self, password: str) -> str:
        """
        Hash a password using Argon2id (or PBKDF2 fallback).

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        if not password:
            raise ValueError("Password cannot be empty")

        if ARGON2_AVAILABLE and self._hasher:
            hashed = self._hasher.hash(password)
            app_logger.debug("Password hashed with Argon2id")
            return hashed
        else:
            # PBKDF2 fallback
            import os
            salt = os.urandom(32)
            hashed = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                iterations=480000,
            )
            result = salt.hex() + ':' + hashed.hex()
            app_logger.debug("Password hashed with PBKDF2 (fallback)")
            return result

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify a password against its hash.

        Uses hmac.compare_digest for timing-safe comparison
        when using PBKDF2 fallback.

        Args:
            password: Plain text password to verify
            hashed: Stored hash to compare against

        Returns:
            True if password matches
        """
        if not password or not hashed:
            return False

        if ARGON2_AVAILABLE and self._hasher and hashed.startswith('$argon2'):
            try:
                return self._hasher.verify(hashed, password)
            except VerifyMismatchError:
                return False
            except (VerificationError, InvalidHashError) as e:
                app_logger.error(f"Password verification error: {e}")
                return False
        else:
            # PBKDF2 fallback verification
            try:
                parts = hashed.split(':')
                if len(parts) != 2:
                    return False

                salt = bytes.fromhex(parts[0])
                stored_hash = parts[1]

                computed = hashlib.pbkdf2_hmac(
                    'sha256',
                    password.encode('utf-8'),
                    salt,
                    iterations=480000,
                ).hex()

                return hmac.compare_digest(computed, stored_hash)
            except (ValueError, TypeError) as e:
                app_logger.error(f"PBKDF2 verification error: {e}")
                return False

    def needs_rehash(self, hashed: str) -> bool:
        """
        Check if a hash needs to be rehashed (e.g., parameters changed).

        Args:
            hashed: The stored hash

        Returns:
            True if rehash is recommended
        """
        if ARGON2_AVAILABLE and self._hasher and hashed.startswith('$argon2'):
            return self._hasher.check_needs_rehash(hashed)

        # PBKDF2 hashes should be migrated to Argon2
        if ARGON2_AVAILABLE and not hashed.startswith('$argon2'):
            return True

        return False

    # ============================================================
    # Account Lockout
    # ============================================================

    def _get_attempt(self, user_id: int) -> LoginAttempt:
        """Get or create login attempt tracker for user."""
        with self._lock:
            if user_id not in self._login_attempts:
                self._login_attempts[user_id] = LoginAttempt(user_id=user_id)
            return self._login_attempts[user_id]

    def record_failed_attempt(self, user_id: int) -> Tuple[int, bool]:
        """
        Record a failed login attempt.

        Args:
            user_id: User ID

        Returns:
            Tuple of (failed_count, is_now_locked)
        """
        with self._lock:
            attempt = self._get_attempt(user_id)
            attempt.failed_count += 1
            attempt.last_failed = datetime.now()

            is_locked = False
            if attempt.failed_count >= MAX_FAILED_ATTEMPTS:
                attempt.locked_until = datetime.now() + timedelta(
                    minutes=LOCKOUT_DURATION_MINUTES
                )
                is_locked = True
                app_logger.warning(
                    f"Account locked for user {user_id} after "
                    f"{attempt.failed_count} failed attempts"
                )
                audit_logger.log(
                    action="ACCOUNT_LOCKED",
                    table="users",
                    record_id=user_id,
                    details={
                        "failed_attempts": attempt.failed_count,
                        "locked_until": attempt.locked_until.isoformat()
                    }
                )

            return attempt.failed_count, is_locked

    def clear_failed_attempts(self, user_id: int) -> None:
        """Clear failed login attempts after successful login."""
        with self._lock:
            if user_id in self._login_attempts:
                del self._login_attempts[user_id]

    def is_locked_out(self, user_id: int) -> bool:
        """
        Check if a user account is locked.

        Args:
            user_id: User ID

        Returns:
            True if account is currently locked
        """
        with self._lock:
            attempt = self._login_attempts.get(user_id)
            if not attempt or not attempt.locked_until:
                return False

            if datetime.now() >= attempt.locked_until:
                # Lockout expired, clear it
                attempt.locked_until = None
                attempt.failed_count = 0
                return False

            return True

    def get_lockout_remaining(self, user_id: int) -> int:
        """
        Get remaining lockout time in seconds.

        Args:
            user_id: User ID

        Returns:
            Remaining seconds, 0 if not locked
        """
        with self._lock:
            attempt = self._login_attempts.get(user_id)
            if not attempt or not attempt.locked_until:
                return 0

            remaining = (attempt.locked_until - datetime.now()).total_seconds()
            return max(0, int(remaining))

    # ============================================================
    # Authentication
    # ============================================================

    def authenticate(
        self,
        user_id: int,
        password: str,
        stored_hash: str,
        user_name: str = "",
        role: str = ""
    ) -> Tuple[bool, str]:
        """
        Authenticate a user with lockout protection.

        Args:
            user_id: User ID
            password: Plain text password
            stored_hash: Hash from database
            user_name: User display name
            role: User role name

        Returns:
            Tuple of (success, message)
        """
        # Check lockout
        if self.is_locked_out(user_id):
            remaining = self.get_lockout_remaining(user_id)
            msg = f"الحساب مقفل. حاول بعد {remaining // 60} دقيقة"
            audit_logger.log(
                action="LOGIN_BLOCKED",
                table="users",
                record_id=user_id,
                details={"reason": "account_locked", "remaining_seconds": remaining}
            )
            return False, msg

        # Verify password
        if self.verify_password(password, stored_hash):
            # Success
            self.clear_failed_attempts(user_id)

            # Check if rehash is needed
            if self.needs_rehash(stored_hash):
                app_logger.info(
                    f"Password rehash recommended for user {user_id}"
                )

            # Create session
            self._create_session(user_id, user_name, role)

            audit_logger.log(
                action="LOGIN_SUCCESS",
                table="users",
                record_id=user_id,
                details={"role": role}
            )

            return True, "تم تسجيل الدخول بنجاح"
        else:
            # Failed
            failed_count, is_locked = self.record_failed_attempt(user_id)

            audit_logger.log(
                action="LOGIN_FAILED",
                table="users",
                record_id=user_id,
                details={
                    "failed_count": failed_count,
                    "locked": is_locked
                }
            )

            if is_locked:
                msg = (
                    f"تم قفل الحساب بعد {MAX_FAILED_ATTEMPTS} محاولات فاشلة. "
                    f"حاول بعد {LOCKOUT_DURATION_MINUTES} دقيقة"
                )
            else:
                remaining = MAX_FAILED_ATTEMPTS - failed_count
                msg = f"كلمة المرور غير صحيحة. متبقي {remaining} محاولات"

            return False, msg

    # ============================================================
    # Session Management
    # ============================================================

    def _create_session(
        self,
        user_id: int,
        user_name: str,
        role: str
    ) -> UserSession:
        """Create a new user session."""
        with self._lock:
            self._session = UserSession(
                user_id=user_id,
                user_name=user_name,
                role=role,
            )
            app_logger.info(f"Session created for user {user_name}")
            return self._session

    def get_session(self) -> Optional[UserSession]:
        """Get current active session."""
        with self._lock:
            if not self._session or not self._session.is_active:
                return None

            # Check timeout
            elapsed = (datetime.now() - self._session.last_activity).total_seconds()
            if elapsed > SESSION_TIMEOUT_MINUTES * 60:
                app_logger.info(
                    f"Session expired for user {self._session.user_name}"
                )
                self._session.is_active = False
                return None

            return self._session

    def touch_session(self) -> None:
        """Update session last activity timestamp."""
        with self._lock:
            if self._session and self._session.is_active:
                self._session.last_activity = datetime.now()

    def end_session(self) -> None:
        """End the current session (logout)."""
        with self._lock:
            if self._session:
                audit_logger.log(
                    action="LOGOUT",
                    table="users",
                    record_id=self._session.user_id,
                )
                app_logger.info(
                    f"Session ended for user {self._session.user_name}"
                )
                self._session.is_active = False
                self._session = None

    @property
    def is_session_active(self) -> bool:
        """Check if there is an active session."""
        return self.get_session() is not None


# ============================================================
# Singleton Access
# ============================================================

_auth_manager: Optional[AuthManager] = None
_auth_lock = threading.Lock()


def get_auth_manager() -> AuthManager:
    """
    Get the AuthManager singleton (thread-safe).

    Returns:
        AuthManager instance
    """
    global _auth_manager
    if _auth_manager is None:
        with _auth_lock:
            if _auth_manager is None:
                _auth_manager = AuthManager()
    return _auth_manager


def is_argon2_available() -> bool:
    """Check if Argon2 is available."""
    return ARGON2_AVAILABLE
