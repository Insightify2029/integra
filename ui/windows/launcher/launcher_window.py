"""
Launcher Window
===============
Main application launcher window.
Database backup/restore on startup/exit.
Git sync is manual only (via menu).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QDialog, QLabel,
    QProgressBar, QMessageBox, QApplication
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal

from ui.windows.base import BaseWindow
from ui.dialogs import SettingsDialog, ThemesDialog, SyncSettingsDialog

from .launcher_menu import create_launcher_menu
from .launcher_header import create_launcher_header
from .launcher_cards_area import LauncherCardsArea
from .launcher_statusbar import LauncherStatusBar

from core.database.connection import connect
from core.themes import get_stylesheet
from core.sync import SyncWorker, load_sync_config, save_sync_config


class RestoreProgressDialog(QDialog):
    """شاشة تقدم استعادة البيانات."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("استعادة البيانات")
        self.setFixedSize(400, 120)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Label
        self.label = QLabel("جاري استعادة آخر نسخة احتياطية...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.label)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3498db;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
        """)
        layout.addWidget(self.progress)

    def update_progress(self, value, message=""):
        """تحديث التقدم."""
        self.progress.setValue(value)
        if message:
            self.label.setText(message)
        QApplication.processEvents()


class RestoreWorker(QThread):
    """Worker لاستعادة البيانات في الخلفية."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def run(self):
        try:
            from core.sync.db_sync import DatabaseSync

            self.progress.emit(10, "جاري البحث عن النسخ الاحتياطية...")

            db_sync = DatabaseSync()
            backup_info = db_sync.backup_manager.get_latest_backup()

            if backup_info is None:
                self.progress.emit(100, "لا توجد نسخ احتياطية")
                self.finished.emit(True, "لا توجد نسخ احتياطية للاستعادة")
                return

            self.progress.emit(30, f"جاري استعادة ({backup_info.formatted_size})...")

            result = db_sync.restore(
                backup_info=backup_info,
                on_progress=lambda p, m: self.progress.emit(30 + int(p * 0.7), m)
            )

            self.progress.emit(100, "تمت الاستعادة!")
            self.finished.emit(result.success, result.message)

        except Exception as e:
            self.finished.emit(False, str(e))


class LauncherWindow(BaseWindow):
    """
    Main launcher window.
    Shows module cards and provides navigation.
    Database sync on startup, manual Git sync via menu.
    """

    _open_windows = {}

    def __init__(self):
        super().__init__()

        # Connect to database
        connect()

        # Sync system (for manual Git sync only)
        self._sync_worker = None
        self._sync_timer = QTimer()
        self._sync_timer.timeout.connect(self._auto_sync)

        # Setup UI
        self._setup_ui()
        self._setup_connections()

        # Maximize on start
        self.showMaximized()

        # استعادة آخر backup عند الفتح
        self._restore_on_startup()

    def _setup_ui(self):
        """Setup the window UI."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = create_launcher_header()
        layout.addWidget(header)

        # Cards area
        self.cards_area = LauncherCardsArea()
        layout.addWidget(self.cards_area, 1)

        layout.addStretch()

        # Menu bar
        self.menu_actions = create_launcher_menu(self)

        # قائمة المزامنة (Git يدوي فقط)
        sync_menu = self.menuBar().addMenu("🔄 المزامنة")

        # Database actions
        self._db_backup_action = sync_menu.addAction("💾 نسخ احتياطي (Backup)")
        self._db_restore_action = sync_menu.addAction("📥 استعادة (Restore)")

        sync_menu.addSeparator()

        # Git actions (يدوي)
        self._sync_pull_action = sync_menu.addAction("⬇️ جلب من Git (Pull)")
        self._sync_push_action = sync_menu.addAction("⬆️ رفع إلى Git (Push)")

        sync_menu.addSeparator()
        self._sync_settings_action = sync_menu.addAction("⚙️ إعدادات المزامنة")

        # Status bar
        self.status_bar = LauncherStatusBar()
        self.setStatusBar(self.status_bar)

    def _setup_connections(self):
        """Setup signal connections."""
        self.menu_actions['settings'].triggered.connect(self._show_settings)
        self.menu_actions['themes'].triggered.connect(self._show_themes)
        self.menu_actions['exit'].triggered.connect(self.close)

        self.cards_area.module_clicked.connect(self._open_module)

        # Database actions
        self._db_backup_action.triggered.connect(self._do_backup)
        self._db_restore_action.triggered.connect(self._do_restore)

        # Git actions
        self._sync_pull_action.triggered.connect(lambda: self._run_sync("pull"))
        self._sync_push_action.triggered.connect(lambda: self._run_sync("push"))
        self._sync_settings_action.triggered.connect(self._show_sync_settings)

    # ═══════════════════════════════════════════════════════
    # Database Backup/Restore (بدون Git)
    # ═══════════════════════════════════════════════════════

    def _restore_on_startup(self):
        """استعادة آخر نسخة احتياطية عند بدء البرنامج."""
        # عرض شاشة التقدم
        self._restore_dialog = RestoreProgressDialog(self)

        # Worker للاستعادة
        self._restore_worker = RestoreWorker()
        self._restore_worker.progress.connect(self._restore_dialog.update_progress)
        self._restore_worker.finished.connect(self._on_restore_finished)

        # بدء الاستعادة
        self._restore_worker.start()
        self._restore_dialog.exec_()

    def _on_restore_finished(self, success, message):
        """بعد انتهاء الاستعادة."""
        self._restore_dialog.close()

        if success:
            self.status_bar.showMessage(f"✅ {message}")
        else:
            self.status_bar.showMessage(f"⚠️ {message}")

        print(f"[RESTORE] {'✅' if success else '❌'} {message}")

    def _do_backup(self):
        """عمل نسخة احتياطية يدوياً."""
        self.status_bar.showMessage("💾 جاري النسخ الاحتياطي...")
        QApplication.processEvents()

        try:
            from core.sync.db_sync import DatabaseSync
            db_sync = DatabaseSync()
            result = db_sync.backup()

            if result.success:
                self.status_bar.showMessage(f"✅ {result.message}")
                QMessageBox.information(self, "نجح", f"تم النسخ الاحتياطي\n{result.message}")
            else:
                self.status_bar.showMessage(f"❌ {result.message}")
                QMessageBox.warning(self, "فشل", f"فشل النسخ الاحتياطي\n{result.message}")
        except Exception as e:
            self.status_bar.showMessage(f"❌ خطأ")
            QMessageBox.critical(self, "خطأ", str(e))

    def _do_restore(self):
        """استعادة نسخة احتياطية يدوياً."""
        reply = QMessageBox.question(
            self, "تأكيد",
            "هل تريد استعادة آخر نسخة احتياطية؟\nسيتم استبدال البيانات الحالية.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._restore_on_startup()

    # ═══════════════════════════════════════════════════════
    # Git Sync (يدوي فقط من القائمة)
    # ═══════════════════════════════════════════════════════

    def _auto_sync(self):
        """مزامنة دورية - معطلة افتراضياً."""
        pass  # معطلة

    def _run_sync(self, mode: str = "push"):
        """تشغيل Git sync يدوياً."""
        if self._sync_worker and self._sync_worker.isRunning():
            QMessageBox.warning(self, "انتظر", "المزامنة جارية...")
            return

        self._current_sync_mode = mode
        self._sync_worker = SyncWorker(mode=mode)
        self._sync_worker.finished.connect(self._on_sync_finished)
        self._sync_worker.start()

        mode_names = {"pull": "جلب", "push": "رفع"}
        self.status_bar.showMessage(f"🔄 جاري {mode_names.get(mode, mode)}...")

    def _on_sync_finished(self, success, logs):
        """بعد انتهاء Git sync."""
        from datetime import datetime

        config = load_sync_config()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        config["last_sync_time"] = now
        config["last_sync_direction"] = getattr(self, "_current_sync_mode", "")
        save_sync_config(config)

        if success:
            self.status_bar.showMessage(f"✅ تمت المزامنة - {now}")
        else:
            self.status_bar.showMessage(f"⚠️ المزامنة لم تكتمل")

        for log in logs:
            print(f"  [SYNC] {log}")

    def _show_sync_settings(self):
        """عرض إعدادات المزامنة."""
        dialog = SyncSettingsDialog(self)
        dialog.exec_()

    # ═══════════════════════════════════════════════════════
    # Other Methods
    # ═══════════════════════════════════════════════════════

    def _show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def _show_themes(self):
        dialog = ThemesDialog(self)
        if dialog.exec_():
            self.setStyleSheet(get_stylesheet())
            for window in self._open_windows.values():
                if window and window.isVisible():
                    window.setStyleSheet(get_stylesheet())

    def _open_module(self, module_id):
        if module_id in self._open_windows:
            window = self._open_windows[module_id]
            if window and window.isVisible():
                window.activateWindow()
                window.raise_()
                return

        if module_id == "mostahaqat":
            from modules.mostahaqat import MostahaqatWindow
            window = MostahaqatWindow()
            window.show()
            self._open_windows[module_id] = window
        else:
            from ui.dialogs import show_info
            show_info(self, "قريباً", f"موديول {module_id} قيد التطوير")

    def closeEvent(self, event):
        """إغلاق البرنامج - سؤال عن النسخ الاحتياطي."""
        reply = QMessageBox.question(
            self,
            "إغلاق البرنامج",
            "هل تريد حفظ نسخة احتياطية قبل الإغلاق؟",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.No
        )

        if reply == QMessageBox.Cancel:
            event.ignore()
            return

        if reply == QMessageBox.Yes:
            try:
                self.status_bar.showMessage("💾 جاري الحفظ...")
                self.repaint()

                from core.sync.db_sync import DatabaseSync
                db_sync = DatabaseSync()
                result = db_sync.backup()
                print(f"[BACKUP] {'✅' if result.success else '❌'} {result.message}")

            except Exception as e:
                print(f"[BACKUP] Error: {e}")

        # إغلاق النوافذ
        for window in self._open_windows.values():
            if window:
                window.close()

        self._sync_timer.stop()
        event.accept()
