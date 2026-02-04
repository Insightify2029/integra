# core/file_watcher/hot_folder.py
"""
INTEGRA - نظام Hot Folder للاستيراد التلقائي
=============================================

نظام مجلدات ذكية لاستيراد الملفات تلقائياً مع معالجة وأرشفة.

البنية:
    hot_folder/
    ├── input/        ← ضع الملفات هنا
    ├── processing/   ← الملفات قيد المعالجة
    ├── archive/      ← الملفات المعالجة بنجاح
    └── error/        ← الملفات التي فشلت معالجتها

الاستخدام:
    from core.file_watcher import HotFolder

    def process_excel(file_path):
        # معالجة الملف
        data = read_excel(file_path)
        import_to_database(data)
        return True  # نجاح

    hot_folder = HotFolder(
        base_path="/path/to/imports",
        processor=process_excel,
        extensions=[".xlsx", ".csv"]
    )
    hot_folder.start()

    # لاحقاً
    hot_folder.stop()
"""

import os
import shutil
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Callable, Dict
from dataclasses import dataclass
from enum import Enum

from PyQt5.QtCore import QObject, pyqtSignal

from .watcher import FileWatcher, is_watchdog_available


# ============================================================
# Constants
# ============================================================

INPUT_FOLDER = "input"
PROCESSING_FOLDER = "processing"
ARCHIVE_FOLDER = "archive"
ERROR_FOLDER = "error"


# ============================================================
# Data Classes
# ============================================================

class ProcessingStatus(Enum):
    """حالة معالجة الملف"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ProcessingResult:
    """نتيجة معالجة ملف"""
    file_path: str
    original_name: str
    status: ProcessingStatus
    message: str = ""
    processed_at: Optional[datetime] = None
    error_details: Optional[str] = None


# ============================================================
# Hot Folder Signals
# ============================================================

class HotFolderSignals(QObject):
    """إشارات للتكامل مع الواجهة"""
    file_detected = pyqtSignal(str)                    # file_path
    processing_started = pyqtSignal(str)               # file_path
    processing_completed = pyqtSignal(str, bool, str)  # file_path, success, message
    processing_error = pyqtSignal(str, str)            # file_path, error
    folder_ready = pyqtSignal()
    folder_stopped = pyqtSignal()


# ============================================================
# Hot Folder Manager
# ============================================================

class HotFolder:
    """
    مدير Hot Folder للاستيراد التلقائي

    يراقب مجلد input ويعالج الملفات الجديدة تلقائياً.
    """

    def __init__(
        self,
        base_path: str,
        processor: Callable[[str], bool],
        extensions: Optional[List[str]] = None,
        auto_archive: bool = True,
        keep_original_name: bool = True,
        add_timestamp: bool = True
    ):
        """
        إنشاء Hot Folder

        Args:
            base_path: المجلد الأساسي (سيتم إنشاء المجلدات الفرعية)
            processor: دالة معالجة الملف (تستقبل المسار وترجع True/False)
            extensions: قائمة الامتدادات المسموحة
            auto_archive: نقل الملفات للأرشيف بعد النجاح
            keep_original_name: الحفاظ على اسم الملف الأصلي
            add_timestamp: إضافة timestamp لاسم الملف في الأرشيف
        """
        if not is_watchdog_available():
            raise ImportError("watchdog غير متاح - pip install watchdog")

        self.base_path = Path(base_path)
        self.processor = processor
        self.extensions = extensions or []
        self.auto_archive = auto_archive
        self.keep_original_name = keep_original_name
        self.add_timestamp = add_timestamp

        # المجلدات
        self.input_path = self.base_path / INPUT_FOLDER
        self.processing_path = self.base_path / PROCESSING_FOLDER
        self.archive_path = self.base_path / ARCHIVE_FOLDER
        self.error_path = self.base_path / ERROR_FOLDER

        # الحالة
        self._signals = HotFolderSignals()
        self._watcher: Optional[FileWatcher] = None
        self._running = False
        self._processing_lock = threading.Lock()
        self._results: List[ProcessingResult] = []

        # إنشاء المجلدات
        self._setup_folders()

    @property
    def signals(self) -> HotFolderSignals:
        """الإشارات للتكامل مع UI"""
        return self._signals

    @property
    def is_running(self) -> bool:
        """هل Hot Folder يعمل؟"""
        return self._running

    def _setup_folders(self):
        """إنشاء هيكل المجلدات"""
        for folder in [self.input_path, self.processing_path,
                       self.archive_path, self.error_path]:
            folder.mkdir(parents=True, exist_ok=True)

    def start(self) -> bool:
        """بدء مراقبة Hot Folder"""
        if self._running:
            return True

        try:
            # إنشاء المراقب
            self._watcher = FileWatcher()

            # ربط الإشارات
            self._watcher.signals.file_stable.connect(self._on_file_ready)
            self._watcher.signals.error.connect(self._on_watcher_error)

            # إضافة مجلد input للمراقبة
            self._watcher.add_watch(
                str(self.input_path),
                extensions=self.extensions,
                stability_seconds=2.0
            )

            # بدء المراقبة
            self._watcher.start()
            self._running = True

            # معالجة الملفات الموجودة مسبقاً
            self._process_existing_files()

            self._signals.folder_ready.emit()
            return True

        except Exception as e:
            self._signals.processing_error.emit("", f"خطأ في البدء: {e}")
            return False

    def stop(self):
        """إيقاف Hot Folder"""
        if not self._running:
            return

        if self._watcher:
            self._watcher.stop()
            self._watcher = None

        self._running = False
        self._signals.folder_stopped.emit()

    def _process_existing_files(self):
        """معالجة الملفات الموجودة في input"""
        if not self.input_path.exists():
            return

        for file_path in self.input_path.iterdir():
            if file_path.is_file():
                if not self.extensions or file_path.suffix.lower() in [e.lower() for e in self.extensions]:
                    self._process_file(str(file_path))

    def _on_file_ready(self, file_path: str):
        """معالج الملف الجاهز"""
        # التأكد أن الملف في مجلد input
        if Path(file_path).parent != self.input_path:
            return

        self._signals.file_detected.emit(file_path)
        self._process_file(file_path)

    def _on_watcher_error(self, path: str, error: str):
        """معالج أخطاء المراقب"""
        self._signals.processing_error.emit(path, error)

    def _process_file(self, file_path: str):
        """معالجة ملف واحد"""
        with self._processing_lock:
            self._do_process_file(file_path)

    def _do_process_file(self, file_path: str):
        """المعالجة الفعلية للملف"""
        original_path = Path(file_path)
        original_name = original_path.name

        if not original_path.exists():
            return

        # نقل للمعالجة
        processing_file = self.processing_path / original_name
        try:
            shutil.move(str(original_path), str(processing_file))
        except Exception as e:
            self._signals.processing_error.emit(
                file_path, f"فشل نقل الملف للمعالجة: {e}"
            )
            return

        self._signals.processing_started.emit(str(processing_file))

        # المعالجة
        success = False
        message = ""
        error_details = None

        try:
            success = self.processor(str(processing_file))
            message = "تمت المعالجة بنجاح" if success else "فشلت المعالجة"
        except Exception as e:
            success = False
            message = "خطأ أثناء المعالجة"
            error_details = str(e)

        # تحديد الوجهة
        if success and self.auto_archive:
            dest_folder = self.archive_path
        elif not success:
            dest_folder = self.error_path
        else:
            dest_folder = None  # إبقاء في processing

        # نقل الملف
        if dest_folder:
            dest_name = self._get_dest_name(original_name)
            dest_path = dest_folder / dest_name

            try:
                shutil.move(str(processing_file), str(dest_path))
            except Exception as e:
                error_details = f"فشل النقل: {e}"

        # تسجيل النتيجة
        result = ProcessingResult(
            file_path=file_path,
            original_name=original_name,
            status=ProcessingStatus.SUCCESS if success else ProcessingStatus.ERROR,
            message=message,
            processed_at=datetime.now(),
            error_details=error_details
        )
        self._results.append(result)

        # إرسال الإشارة
        self._signals.processing_completed.emit(file_path, success, message)

        if error_details:
            self._signals.processing_error.emit(file_path, error_details)

    def _get_dest_name(self, original_name: str) -> str:
        """توليد اسم الملف في الوجهة"""
        if not self.add_timestamp:
            return original_name

        path = Path(original_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self.keep_original_name:
            return f"{path.stem}_{timestamp}{path.suffix}"
        else:
            return f"{timestamp}{path.suffix}"

    def get_results(self) -> List[ProcessingResult]:
        """الحصول على نتائج المعالجة"""
        return self._results.copy()

    def get_stats(self) -> Dict:
        """الحصول على إحصائيات"""
        total = len(self._results)
        success = sum(1 for r in self._results if r.status == ProcessingStatus.SUCCESS)
        error = sum(1 for r in self._results if r.status == ProcessingStatus.ERROR)

        return {
            "total": total,
            "success": success,
            "error": error,
            "success_rate": (success / total * 100) if total > 0 else 0
        }

    def clear_results(self):
        """مسح سجل النتائج"""
        self._results.clear()

    def retry_errors(self) -> int:
        """إعادة محاولة الملفات الفاشلة"""
        count = 0
        for file_path in self.error_path.iterdir():
            if file_path.is_file():
                # نقل للـ input
                dest = self.input_path / file_path.name
                try:
                    shutil.move(str(file_path), str(dest))
                    count += 1
                except Exception:
                    pass
        return count


# ============================================================
# Convenience Functions
# ============================================================

def create_hot_folder(
    base_path: str,
    processor: Callable[[str], bool],
    extensions: Optional[List[str]] = None,
    auto_start: bool = True
) -> HotFolder:
    """
    إنشاء Hot Folder بطريقة مبسطة

    Args:
        base_path: المجلد الأساسي
        processor: دالة المعالجة
        extensions: الامتدادات المسموحة
        auto_start: بدء تلقائي

    Returns:
        HotFolder instance

    Example:
        def process_file(path):
            print(f"Processing: {path}")
            return True

        folder = create_hot_folder(
            "/imports",
            process_file,
            extensions=[".xlsx", ".csv"]
        )
    """
    hot_folder = HotFolder(
        base_path=base_path,
        processor=processor,
        extensions=extensions
    )

    if auto_start:
        hot_folder.start()

    return hot_folder
