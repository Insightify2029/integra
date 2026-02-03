"""
Launcher Window
===============
Main application launcher window.
Includes full sync automation (Git + Database).
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer

from ui.windows.base import BaseWindow
from ui.dialogs import SettingsDialog, ThemesDialog, SyncSettingsDialog

from .launcher_menu import create_launcher_menu
from .launcher_header import create_launcher_header
from .launcher_cards_area import LauncherCardsArea
from .launcher_statusbar import LauncherStatusBar

from core.database.connection import connect
from core.themes import get_stylesheet
from core.sync import SyncWorker, load_sync_config, save_sync_config


class LauncherWindow(BaseWindow):
    """
    Main launcher window.
    Shows module cards and provides navigation.
    Includes automated sync system (Git + Database).
    """

    # Store references to open module windows
    _open_windows = {}

    def __init__(self):
        super().__init__()

        # Connect to database
        connect()

        # Sync system
        self._sync_worker = None
        self._sync_timer = QTimer()
        self._sync_timer.timeout.connect(self._auto_sync)

        # Setup UI
        self._setup_ui()
        self._setup_connections()

        # Maximize on start
        self.showMaximized()

        # Startup sync (PULL mode: git pull + database restore)
        self._init_sync()

    def _setup_ui(self):
        """Setup the window UI."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header (INTEGRA logo)
        header = create_launcher_header()
        layout.addWidget(header)

        # Cards area
        self.cards_area = LauncherCardsArea()
        layout.addWidget(self.cards_area, 1)

        # Spacer
        layout.addStretch()

        # Menu bar
        self.menu_actions = create_launcher_menu(self)

        # Sync menu
        sync_menu = self.menuBar().addMenu("\U0001f504 \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629")
        self._sync_pull_action = sync_menu.addAction(
            "\u2b07\ufe0f \u062c\u0644\u0628 + \u0627\u0633\u062a\u0639\u0627\u062f\u0629 (Pull)"
        )
        self._sync_push_action = sync_menu.addAction(
            "\u2b06\ufe0f \u0646\u0633\u062e + \u0631\u0641\u0639 (Push)"
        )
        self._sync_full_action = sync_menu.addAction(
            "\U0001f504 \u0645\u0632\u0627\u0645\u0646\u0629 \u0643\u0627\u0645\u0644\u0629 (Full)"
        )
        sync_menu.addSeparator()
        self._sync_settings_action = sync_menu.addAction(
            "\u2699\ufe0f \u0625\u0639\u062f\u0627\u062f\u0627\u062a \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629"
        )

        # Status bar
        self.status_bar = LauncherStatusBar()
        self.setStatusBar(self.status_bar)

    def _setup_connections(self):
        """Setup signal connections."""
        # Menu actions
        self.menu_actions['settings'].triggered.connect(self._show_settings)
        self.menu_actions['themes'].triggered.connect(self._show_themes)
        self.menu_actions['exit'].triggered.connect(self.close)

        # Module cards
        self.cards_area.module_clicked.connect(self._open_module)

        # Sync actions
        self._sync_pull_action.triggered.connect(lambda: self._run_sync("pull"))
        self._sync_push_action.triggered.connect(lambda: self._run_sync("push"))
        self._sync_full_action.triggered.connect(lambda: self._run_sync("full"))
        self._sync_settings_action.triggered.connect(self._show_sync_settings)

    # ═══════════════════════════════════════════════════════
    # Sync Methods - Full Automation
    # ═══════════════════════════════════════════════════════

    def _init_sync(self):
        """تهيئة نظام المزامنة عند بدء البرنامج."""
        config = load_sync_config()

        # تشغيل المزامنة الدورية لو مفعّلة
        if config.get("auto_sync_enabled", False):
            interval = config.get("auto_sync_interval_minutes", 30)
            self._sync_timer.start(interval * 60 * 1000)

        # مزامنة عند الفتح (PULL: git pull + database restore)
        if config.get("sync_on_startup", True):
            self.status_bar.showMessage(
                "\U0001f504 \u062c\u0627\u0631\u064a \u062c\u0644\u0628 \u0627\u0644\u062a\u062d\u062f\u064a\u062b\u0627\u062a + \u0627\u0633\u062a\u0639\u0627\u062f\u0629 \u0627\u0644\u062f\u0627\u062a\u0627\u0628\u064a\u0632..."
            )
            self._run_sync("pull")

    def _auto_sync(self):
        """مزامنة دورية تلقائية (PUSH mode)."""
        if self._sync_worker and self._sync_worker.isRunning():
            return
        self.status_bar.showMessage(
            "\U0001f504 \u0645\u0632\u0627\u0645\u0646\u0629 \u062f\u0648\u0631\u064a\u0629..."
        )
        self._run_sync("push")

    def _run_sync(self, mode: str = "push"):
        """تشغيل المزامنة في الخلفية."""
        if self._sync_worker and self._sync_worker.isRunning():
            return

        self._current_sync_mode = mode
        self._sync_worker = SyncWorker(mode=mode)
        self._sync_worker.finished.connect(self._on_sync_finished)
        self._sync_worker.start()

        mode_names = {
            "pull": "\u062c\u0644\u0628 + \u0627\u0633\u062a\u0639\u0627\u062f\u0629",
            "push": "\u0646\u0633\u062e + \u0631\u0641\u0639",
            "full": "\u0645\u0632\u0627\u0645\u0646\u0629 \u0643\u0627\u0645\u0644\u0629"
        }
        self.status_bar.showMessage(
            f"\U0001f504 \u062c\u0627\u0631\u064a: {mode_names.get(mode, mode)}..."
        )

    def _on_sync_finished(self, success, logs):
        """بعد انتهاء المزامنة."""
        from datetime import datetime

        # تحديث وقت آخر مزامنة
        config = load_sync_config()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        config["last_sync_time"] = now
        config["last_sync_direction"] = getattr(self, "_current_sync_mode", "")
        save_sync_config(config)

        mode = getattr(self, "_current_sync_mode", "")
        mode_icons = {"pull": "\u2b07\ufe0f", "push": "\u2b06\ufe0f", "full": "\U0001f504"}
        icon = mode_icons.get(mode, "\U0001f504")

        if success:
            self.status_bar.showMessage(
                f"\u2705 \u062a\u0645\u062a \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629 {icon} - {now}"
            )
        else:
            self.status_bar.showMessage(
                f"\u26a0\ufe0f \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629 \u0644\u0645 \u062a\u0643\u062a\u0645\u0644 {icon}"
            )

        # طباعة السجل في الكونسول
        for log in logs:
            print(f"  [SYNC] {log}")

    def _show_sync_settings(self):
        """عرض شاشة إعدادات المزامنة."""
        dialog = SyncSettingsDialog(self)
        if dialog.exec_():
            # إعادة ضبط المؤقت حسب الإعدادات الجديدة
            config = load_sync_config()
            if config.get("auto_sync_enabled", False):
                interval = config.get("auto_sync_interval_minutes", 30)
                self._sync_timer.start(interval * 60 * 1000)
            else:
                self._sync_timer.stop()

    # ═══════════════════════════════════════════════════════
    # Existing Methods
    # ═══════════════════════════════════════════════════════

    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec_()

    def _show_themes(self):
        """Show themes dialog."""
        dialog = ThemesDialog(self)
        if dialog.exec_():
            # Refresh theme
            self.setStyleSheet(get_stylesheet())

            # Refresh all open windows
            for window in self._open_windows.values():
                if window and window.isVisible():
                    window.setStyleSheet(get_stylesheet())

    def _open_module(self, module_id):
        """Open a module window."""
        # Check if already open
        if module_id in self._open_windows:
            window = self._open_windows[module_id]
            if window and window.isVisible():
                window.activateWindow()
                window.raise_()
                return

        # Open new window based on module
        if module_id == "mostahaqat":
            from modules.mostahaqat import MostahaqatWindow
            window = MostahaqatWindow()
            window.show()
            self._open_windows[module_id] = window
        else:
            # Module not implemented yet
            from ui.dialogs import show_info
            show_info(self, "\u0642\u0631\u064a\u0628\u0627\u064b", f"\u0645\u0648\u062f\u064a\u0648\u0644 {module_id} \u0642\u064a\u062f \u0627\u0644\u062a\u0637\u0648\u064a\u0631")

    def closeEvent(self, event):
        """Handle window close - سؤال المستخدم عن النسخ الاحتياطي."""
        from PyQt5.QtWidgets import QMessageBox

        # سؤال المستخدم
        reply = QMessageBox.question(
            self,
            "إغلاق البرنامج",
            "هل تريد حفظ نسخة احتياطية من قاعدة البيانات؟",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.No  # الافتراضي: لا
        )

        # إلغاء الإغلاق
        if reply == QMessageBox.Cancel:
            event.ignore()
            return

        # حفظ نسخة احتياطية إذا طلب المستخدم
        if reply == QMessageBox.Yes:
            try:
                self.status_bar.showMessage("💾 جاري حفظ النسخة الاحتياطية...")
                self.repaint()

                # Backup فقط (بدون Git)
                from core.sync.db_sync import DatabaseSync
                db_sync = DatabaseSync()
                result = db_sync.backup()

                if result.success:
                    print(f"[BACKUP] ✅ {result.message}")
                else:
                    print(f"[BACKUP] ❌ {result.message}")

            except Exception as e:
                print(f"[BACKUP] Error: {e}")

        # إغلاق كل النوافذ المفتوحة
        for window in self._open_windows.values():
            if window:
                window.close()

        # إيقاف المؤقت
        self._sync_timer.stop()

        event.accept()
