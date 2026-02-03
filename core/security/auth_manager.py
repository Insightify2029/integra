# -*- coding: utf-8 -*-
"""
Authentication Manager
======================
User authentication with Argon2 password hashing.

Features:
  - Argon2id password hashing (memory-hard, GPU-resistant)
  - Account lockout after failed attempts
  - Session management
  - Password strength validation
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import secrets
import re

# Try to import argon2, provide fallback
try:
    from argon2 import PasswordHasher, exceptions as argon2_exceptions
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False
    # Fallback to hashlib (less secure but functional)
    import hashlib


@dataclass
class UserSession:
    """Active user session."""
    user_id: int
    username: str
    token: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    roles: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


@dataclass
class LoginAttempt:
    """Track login attempts for lockout."""
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    locked_until: Optional[datetime] = None

    @property
    def is_locked(self) -> bool:
        """Check if account is locked."""
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until


class AuthManager:
    """
    Authentication manager with Argon2 password hashing.

    Usage:
        auth = AuthManager()

        # Hash password for storage
        hashed = auth.hash_password("user_password")

        # Verify password
        if auth.verify_password("user_password", hashed):
            print("Password correct!")

        # Login with lockout protection
        success, session = auth.login(username, password)
    """

    # Configuration
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    SESSION_DURATION_HOURS = 8

    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = False

    def __init__(self):
        """Initialize authentication manager."""
        self._hasher = PasswordHasher() if ARGON2_AVAILABLE else None
        self._sessions: Dict[str, UserSession] = {}
        self._login_attempts: Dict[str, LoginAttempt] = {}
        self._current_user: Optional[UserSession] = None

    def hash_password(self, password: str) -> str:
        """
        Hash a password using Argon2id.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        if ARGON2_AVAILABLE:
            return self._hasher.hash(password)
        else:
            # Fallback: SHA-256 with salt (less secure)
            salt = secrets.token_hex(16)
            hashed = hashlib.sha256((salt + password).encode()).hexdigest()
            return f"sha256${salt}${hashed}"

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password to verify
            hashed: The stored hash

        Returns:
            True if password matches
        """
        if ARGON2_AVAILABLE:
            try:
                self._hasher.verify(hashed, password)
                return True
            except argon2_exceptions.VerifyMismatchError:
                return False
            except Exception:
                return False
        else:
            # Fallback verification
            if not hashed.startswith("sha256$"):
                return False
            parts = hashed.split("$")
            if len(parts) != 3:
                return False
            salt, stored_hash = parts[1], parts[2]
            computed = hashlib.sha256((salt + password).encode()).hexdigest()
            return secrets.compare_digest(computed, stored_hash)

    def check_password_strength(self, password: str) -> Tuple[bool, list]:
        """
        Check password strength against requirements.

        Args:
            password: Password to check

        Returns:
            (is_valid, list_of_issues)
        """
        issues = []

        if len(password) < self.MIN_PASSWORD_LENGTH:
            issues.append(f"كلمة المرور يجب أن تكون {self.MIN_PASSWORD_LENGTH} أحرف على الأقل")

        if self.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            issues.append("يجب أن تحتوي على حرف كبير")

        if self.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            issues.append("يجب أن تحتوي على حرف صغير")

        if self.REQUIRE_DIGIT and not re.search(r'\d', password):
            issues.append("يجب أن تحتوي على رقم")

        if self.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("يجب أن تحتوي على رمز خاص")

        return len(issues) == 0, issues

    def login(
        self,
        username: str,
        password: str,
        verify_func: callable = None
    ) -> Tuple[bool, Optional[UserSession], str]:
        """
        Attempt to log in a user.

        Args:
            username: Username
            password: Plain text password
            verify_func: Optional function(username, password_hash) -> (user_id, roles)
                        If not provided, only checks lockout

        Returns:
            (success, session, message)
        """
        # Check lockout
        attempt = self._login_attempts.get(username, LoginAttempt())

        if attempt.is_locked:
            remaining = (attempt.locked_until - datetime.now()).seconds // 60
            return False, None, f"الحساب مقفل. حاول بعد {remaining} دقيقة"

        # If no verify function, just return (for testing lockout)
        if verify_func is None:
            return False, None, "لم يتم توفير دالة التحقق"

        try:
            # Call verification function
            result = verify_func(username, password)

            if result is None:
                # Failed login
                self._record_failed_attempt(username, attempt)
                remaining = self.MAX_LOGIN_ATTEMPTS - attempt.attempts
                return False, None, f"اسم المستخدم أو كلمة المرور غير صحيحة ({remaining} محاولات متبقية)"

            user_id, roles = result

            # Successful login - reset attempts
            if username in self._login_attempts:
                del self._login_attempts[username]

            # Create session
            session = self._create_session(user_id, username, roles)
            self._current_user = session

            return True, session, "تم تسجيل الدخول بنجاح"

        except Exception as e:
            return False, None, f"خطأ في تسجيل الدخول: {e}"

    def logout(self, token: str = None) -> bool:
        """
        Log out a user session.

        Args:
            token: Session token (if None, logs out current user)

        Returns:
            True if logout successful
        """
        if token is None and self._current_user:
            token = self._current_user.token

        if token and token in self._sessions:
            del self._sessions[token]
            if self._current_user and self._current_user.token == token:
                self._current_user = None
            return True

        return False

    def get_session(self, token: str) -> Optional[UserSession]:
        """Get session by token."""
        session = self._sessions.get(token)
        if session and not session.is_expired:
            return session
        if session and session.is_expired:
            del self._sessions[token]
        return None

    @property
    def current_user(self) -> Optional[UserSession]:
        """Get current logged in user session."""
        return self._current_user

    @property
    def is_authenticated(self) -> bool:
        """Check if a user is currently logged in."""
        return self._current_user is not None and not self._current_user.is_expired

    def _create_session(
        self,
        user_id: int,
        username: str,
        roles: list = None
    ) -> UserSession:
        """Create a new user session."""
        token = secrets.token_urlsafe(32)
        session = UserSession(
            user_id=user_id,
            username=username,
            token=token,
            expires_at=datetime.now() + timedelta(hours=self.SESSION_DURATION_HOURS),
            roles=roles or []
        )
        self._sessions[token] = session
        return session

    def _record_failed_attempt(self, username: str, attempt: LoginAttempt):
        """Record a failed login attempt."""
        attempt.attempts += 1
        attempt.last_attempt = datetime.now()

        if attempt.attempts >= self.MAX_LOGIN_ATTEMPTS:
            attempt.locked_until = datetime.now() + timedelta(
                minutes=self.LOCKOUT_DURATION_MINUTES
            )

        self._login_attempts[username] = attempt


# Singleton instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get the global AuthManager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


# Convenience functions

def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return get_auth_manager().hash_password(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return get_auth_manager().verify_password(password, hashed)
