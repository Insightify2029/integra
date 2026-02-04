# core/file_watcher/__init__.py
"""
INTEGRA - نظام مراقبة الملفات (watchdog)
=========================================

نظام مراقبة ملفات متكامل للكشف عن الملفات الجديدة ومعالجتها.

الاستخدام البسيط - مراقبة مجلد:
    from core.file_watcher import watch_folder

    watcher = watch_folder(
        path="/path/to/folder",
        on_file_stable=process_file,
        extensions=[".xlsx", ".csv"]
    )

    # لاحقاً
    watcher.stop()

الاستخدام المتقدم - Hot Folder للاستيراد:
    from core.file_watcher import HotFolder

    def process_import(file_path):
        data = read_excel(file_path)
        import_to_database(data)
        return True

    folder = HotFolder(
        base_path="/imports",
        processor=process_import,
        extensions=[".xlsx"]
    )
    folder.signals.processing_completed.connect(on_done)
    folder.start()

بنية Hot Folder:
    base_path/
    ├── input/        ← ضع الملفات هنا
    ├── processing/   ← قيد المعالجة
    ├── archive/      ← نجاح
    └── error/        ← فشل
"""

from .watcher import (
    # Classes
    FileWatcher,
    WatcherSignals,
    INTEGRAEventHandler,
    FileEvent,

    # Singleton
    get_file_watcher,
    is_watchdog_available,

    # Convenience
    watch_folder,
    stop_all_watchers,

    # Constants
    DEFAULT_DEBOUNCE_SECONDS,
    DEFAULT_STABILITY_SECONDS,
)

from .hot_folder import (
    # Classes
    HotFolder,
    HotFolderSignals,
    ProcessingResult,
    ProcessingStatus,

    # Convenience
    create_hot_folder,

    # Constants
    INPUT_FOLDER,
    PROCESSING_FOLDER,
    ARCHIVE_FOLDER,
    ERROR_FOLDER,
)

__all__ = [
    # Watcher Classes
    'FileWatcher',
    'WatcherSignals',
    'INTEGRAEventHandler',
    'FileEvent',

    # Watcher Singleton & Functions
    'get_file_watcher',
    'is_watchdog_available',
    'watch_folder',
    'stop_all_watchers',

    # Watcher Constants
    'DEFAULT_DEBOUNCE_SECONDS',
    'DEFAULT_STABILITY_SECONDS',

    # Hot Folder Classes
    'HotFolder',
    'HotFolderSignals',
    'ProcessingResult',
    'ProcessingStatus',

    # Hot Folder Functions
    'create_hot_folder',

    # Hot Folder Constants
    'INPUT_FOLDER',
    'PROCESSING_FOLDER',
    'ARCHIVE_FOLDER',
    'ERROR_FOLDER',
]
