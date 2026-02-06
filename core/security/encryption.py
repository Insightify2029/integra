# core/security/encryption.py
"""
INTEGRA - نظام تشفير البيانات الحساسة
=====================================

نظام تشفير آمن للبيانات الحساسة باستخدام Fernet (AES-128-CBC).

الميزات:
- تشفير متماثل (Symmetric) باستخدام Fernet
- إدارة مفاتيح التشفير
- تخزين آمن للمفاتيح
- تشفير/فك تشفير النصوص والملفات
- دعم تشفير حقول قاعدة البيانات

الاستخدام:
    from core.security import encrypt, decrypt, get_encryptor

    # تشفير بسيط
    encrypted = encrypt("نص سري")
    decrypted = decrypt(encrypted)

    # تشفير ملف
    encrypt_file("secret.txt", "secret.enc")
    decrypt_file("secret.enc", "secret_restored.txt")

    # تشفير IBAN أو كلمة مرور
    encrypted_iban = encrypt("SA0380000000608010167519")
"""

import os
import base64
import json
import hmac
import hashlib
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any
from datetime import datetime

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None
    InvalidToken = Exception

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


# ============================================================
# Constants
# ============================================================

APP_NAME = "INTEGRA"
KEY_NAME = "encryption_key"
KEY_FILE = Path(__file__).parent.parent.parent / ".encryption_key"
SALT_FILE = Path(__file__).parent.parent.parent / ".encryption_salt"


# ============================================================
# Key Management
# ============================================================

def _generate_key() -> bytes:
    """توليد مفتاح تشفير جديد"""
    if not CRYPTOGRAPHY_AVAILABLE:
        raise ImportError("cryptography غير متاح - pip install cryptography")
    return Fernet.generate_key()


def _derive_key_from_password(password: str, salt: bytes) -> bytes:
    """اشتقاق مفتاح من كلمة مرور"""
    if not CRYPTOGRAPHY_AVAILABLE:
        raise ImportError("cryptography غير متاح")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def _get_or_create_salt() -> bytes:
    """الحصول على أو إنشاء salt"""
    if SALT_FILE.exists():
        return SALT_FILE.read_bytes()
    else:
        salt = os.urandom(16)
        SALT_FILE.write_bytes(salt)
        return salt


def _store_key_in_keyring(key: bytes) -> bool:
    """تخزين المفتاح في keyring النظام"""
    if not KEYRING_AVAILABLE:
        return False
    try:
        keyring.set_password(APP_NAME, KEY_NAME, key.decode())
        return True
    except Exception:
        return False


def _get_key_from_keyring() -> Optional[bytes]:
    """استرجاع المفتاح من keyring"""
    if not KEYRING_AVAILABLE:
        return None
    try:
        key = keyring.get_password(APP_NAME, KEY_NAME)
        return key.encode() if key else None
    except Exception:
        return None


def _store_key_in_file(key: bytes):
    """تخزين المفتاح في ملف (أقل أماناً)"""
    logger = logging.getLogger(__name__)
    logger.warning("Storing encryption key in file (keyring unavailable). "
                   "Consider installing keyring for better security.")
    KEY_FILE.write_bytes(key)
    # تعيين صلاحيات محدودة (owner only)
    try:
        os.chmod(KEY_FILE, 0o600)
    except Exception:
        logger.warning("Could not set restricted permissions on key file")


def _get_key_from_file() -> Optional[bytes]:
    """استرجاع المفتاح من ملف"""
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    return None


# ============================================================
# Encryptor Class
# ============================================================

class Encryptor:
    """
    مدير التشفير

    يوفر واجهة موحدة لتشفير وفك تشفير البيانات.
    """

    _instance = None
    _cls_lock = __import__('threading').Lock()

    def __new__(cls):
        """Singleton pattern (thread-safe)"""
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
        self._fernet: Optional[Fernet] = None
        self._key: Optional[bytes] = None

        # محاولة تحميل المفتاح
        self._load_or_create_key()

    def _load_or_create_key(self):
        """تحميل أو إنشاء مفتاح التشفير"""
        if not CRYPTOGRAPHY_AVAILABLE:
            return

        # محاولة من keyring أولاً
        self._key = _get_key_from_keyring()

        # ثم من الملف
        if not self._key:
            self._key = _get_key_from_file()
            # محاولة ترحيل المفتاح من الملف إلى keyring
            if self._key and _store_key_in_keyring(self._key):
                try:
                    KEY_FILE.unlink()
                except Exception:
                    pass

        # إنشاء مفتاح جديد
        if not self._key:
            self._key = _generate_key()
            # محاولة التخزين في keyring
            if not _store_key_in_keyring(self._key):
                # التخزين في ملف كبديل
                _store_key_in_file(self._key)

        # إنشاء Fernet
        self._fernet = Fernet(self._key)

    @property
    def is_available(self) -> bool:
        """هل التشفير متاح؟"""
        return CRYPTOGRAPHY_AVAILABLE and self._fernet is not None

    def encrypt(self, data: Union[str, bytes]) -> str:
        """
        تشفير بيانات

        Args:
            data: النص أو البيانات للتشفير

        Returns:
            النص المشفر (base64)
        """
        if not self.is_available:
            raise RuntimeError("التشفير غير متاح")

        if isinstance(data, str):
            data = data.encode('utf-8')

        encrypted = self._fernet.encrypt(data)
        return encrypted.decode('utf-8')

    def decrypt(self, encrypted_data: str) -> str:
        """
        فك تشفير بيانات

        Args:
            encrypted_data: النص المشفر

        Returns:
            النص الأصلي

        Raises:
            ValueError: إذا كان التشفير غير صالح
        """
        if not self.is_available:
            raise RuntimeError("التشفير غير متاح")

        try:
            decrypted = self._fernet.decrypt(encrypted_data.encode('utf-8'))
            return decrypted.decode('utf-8')
        except InvalidToken:
            raise ValueError("فشل فك التشفير - البيانات تالفة أو المفتاح خاطئ")

    def encrypt_dict(self, data: Dict[str, Any], fields: Optional[list] = None) -> Dict[str, Any]:
        """
        تشفير حقول معينة في قاموس

        Args:
            data: القاموس
            fields: الحقول المراد تشفيرها (None = كل الحقول)

        Returns:
            القاموس مع الحقول المشفرة
        """
        result = data.copy()
        fields_to_encrypt = fields or list(data.keys())

        for field in fields_to_encrypt:
            if field in result and result[field]:
                value = result[field]
                if isinstance(value, (str, bytes)):
                    result[field] = self.encrypt(value)

        return result

    def decrypt_dict(self, data: Dict[str, Any], fields: Optional[list] = None) -> Dict[str, Any]:
        """
        فك تشفير حقول معينة في قاموس

        Args:
            data: القاموس المشفر
            fields: الحقول المراد فك تشفيرها

        Returns:
            القاموس مع الحقول المفكوكة
        """
        result = data.copy()
        fields_to_decrypt = fields or list(data.keys())

        for field in fields_to_decrypt:
            if field in result and result[field]:
                try:
                    result[field] = self.decrypt(result[field])
                except (ValueError, Exception):
                    pass  # الحقل غير مشفر أو تالف

        return result

    def encrypt_file(self, input_path: str, output_path: str) -> bool:
        """
        تشفير ملف

        Args:
            input_path: مسار الملف الأصلي
            output_path: مسار الملف المشفر

        Returns:
            True إذا نجح
        """
        if not self.is_available:
            return False

        try:
            with open(input_path, 'rb') as f:
                data = f.read()

            encrypted = self._fernet.encrypt(data)

            with open(output_path, 'wb') as f:
                f.write(encrypted)

            return True
        except Exception:
            return False

    def decrypt_file(self, input_path: str, output_path: str) -> bool:
        """
        فك تشفير ملف

        Args:
            input_path: مسار الملف المشفر
            output_path: مسار الملف المفكوك

        Returns:
            True إذا نجح
        """
        if not self.is_available:
            return False

        try:
            with open(input_path, 'rb') as f:
                encrypted = f.read()

            decrypted = self._fernet.decrypt(encrypted)

            with open(output_path, 'wb') as f:
                f.write(decrypted)

            return True
        except Exception:
            return False

    def hash_password(self, password: str) -> str:
        """
        تجزئة كلمة مرور (one-way hash)

        Args:
            password: كلمة المرور

        Returns:
            الـ hash
        """
        salt = _get_or_create_salt()
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt,
            100000
        ).hex()

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        التحقق من كلمة مرور

        Args:
            password: كلمة المرور للتحقق
            hashed: الـ hash المخزن

        Returns:
            True إذا تطابقت
        """
        return hmac.compare_digest(self.hash_password(password), hashed)

    def rotate_key(
        self,
        new_key: Optional[bytes] = None,
        re_encrypt_values: Optional[list] = None
    ) -> tuple:
        """
        تدوير المفتاح مع إعادة تشفير البيانات اختيارياً

        Args:
            new_key: مفتاح جديد (اختياري، يُولّد تلقائياً)
            re_encrypt_values: قائمة نصوص مشفرة بالمفتاح القديم لإعادة تشفيرها

        Returns:
            tuple: (المفتاح الجديد, قائمة القيم المعاد تشفيرها أو None)
        """
        old_fernet = self._fernet
        re_encrypted = None

        # فك تشفير البيانات بالمفتاح القديم أولاً
        if re_encrypt_values and old_fernet:
            decrypted_values = []
            for val in re_encrypt_values:
                try:
                    decrypted = old_fernet.decrypt(val.encode('utf-8')).decode('utf-8')
                    decrypted_values.append(decrypted)
                except Exception:
                    decrypted_values.append(None)
        else:
            decrypted_values = None

        # تحديث المفتاح
        if new_key is None:
            new_key = _generate_key()

        self._key = new_key
        self._fernet = Fernet(self._key)

        # تحديث التخزين
        if not _store_key_in_keyring(self._key):
            _store_key_in_file(self._key)

        # إعادة تشفير بالمفتاح الجديد
        if decrypted_values is not None:
            re_encrypted = []
            for val in decrypted_values:
                if val is not None:
                    re_encrypted.append(self.encrypt(val))
                else:
                    re_encrypted.append(None)

        return self._key, re_encrypted


# ============================================================
# Singleton Access
# ============================================================

_encryptor: Optional[Encryptor] = None
_encryptor_lock = __import__('threading').Lock()


def get_encryptor() -> Encryptor:
    """
    الحصول على مدير التشفير (thread-safe)

    Returns:
        Encryptor singleton instance
    """
    global _encryptor
    if _encryptor is None:
        with _encryptor_lock:
            if _encryptor is None:
                _encryptor = Encryptor()
    return _encryptor


def is_encryption_available() -> bool:
    """هل التشفير متاح؟"""
    return CRYPTOGRAPHY_AVAILABLE


# ============================================================
# Convenience Functions
# ============================================================

def encrypt(data: Union[str, bytes]) -> str:
    """
    تشفير بيانات

    Example:
        encrypted = encrypt("بيانات سرية")
    """
    return get_encryptor().encrypt(data)


def decrypt(encrypted_data: str) -> str:
    """
    فك تشفير بيانات

    Example:
        original = decrypt(encrypted)
    """
    return get_encryptor().decrypt(encrypted_data)


def encrypt_sensitive_fields(
    data: Dict[str, Any],
    fields: list = None
) -> Dict[str, Any]:
    """
    تشفير حقول حساسة في قاموس

    Example:
        employee = encrypt_sensitive_fields(
            employee_data,
            fields=['iban', 'password', 'ssn']
        )
    """
    return get_encryptor().encrypt_dict(data, fields)


def decrypt_sensitive_fields(
    data: Dict[str, Any],
    fields: list = None
) -> Dict[str, Any]:
    """
    فك تشفير حقول حساسة

    Example:
        employee = decrypt_sensitive_fields(encrypted_employee, fields=['iban'])
    """
    return get_encryptor().decrypt_dict(data, fields)


def encrypt_file(input_path: str, output_path: str) -> bool:
    """
    تشفير ملف

    Example:
        encrypt_file("secret.txt", "secret.enc")
    """
    return get_encryptor().encrypt_file(input_path, output_path)


def decrypt_file(input_path: str, output_path: str) -> bool:
    """
    فك تشفير ملف

    Example:
        decrypt_file("secret.enc", "secret.txt")
    """
    return get_encryptor().decrypt_file(input_path, output_path)


def hash_password(password: str) -> str:
    """
    تجزئة كلمة مرور

    Example:
        hashed = hash_password("mypassword123")
    """
    return get_encryptor().hash_password(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    التحقق من كلمة مرور

    Example:
        if verify_password(input_password, stored_hash):
            print("Password correct!")
    """
    return get_encryptor().verify_password(password, hashed)


# ============================================================
# Sensitive Data Helpers
# ============================================================

def encrypt_iban(iban: str) -> str:
    """تشفير IBAN"""
    return encrypt(iban)


def decrypt_iban(encrypted_iban: str) -> str:
    """فك تشفير IBAN"""
    return decrypt(encrypted_iban)


def mask_iban(iban: str, visible_chars: int = 4) -> str:
    """
    إخفاء IBAN مع إظهار آخر أحرف

    Example:
        mask_iban("SA0380000000608010167519")
        # Returns: "**********************7519"
    """
    if len(iban) <= visible_chars:
        return iban
    return '*' * (len(iban) - visible_chars) + iban[-visible_chars:]


def encrypt_db_password(password: str) -> str:
    """تشفير كلمة مرور قاعدة البيانات"""
    return encrypt(password)


def decrypt_db_password(encrypted: str) -> str:
    """فك تشفير كلمة مرور قاعدة البيانات"""
    return decrypt(encrypted)
