# -*- coding: utf-8 -*-
"""
Sync Settings Dialog - v2
=========================
شاشة إعدادات المزامنة مع دعم كامل للأوضاع المختلفة
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QSpinBox, QFrame,
    QTextEdit, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.themes import get_current_theme
from core.sync import load_sync_config, save_sync_config, SyncWorker


class SyncSettingsDialog(QDialog):
    """شاشة إعدادات المزامنة."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("\U0001f504 \u0625\u0639\u062f\u0627\u062f\u0627\u062a \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629")
        self.setMinimumSize(600, 600)
        self._worker = None
        self._config = load_sync_config()

        self._setup_ui()
        self._apply_theme()
        self._load_settings()

    def _setup_ui(self):
        """بناء الواجهة."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # === العنوان ===
        title = QLabel("\U0001f504 \u0625\u0639\u062f\u0627\u062f\u0627\u062a \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629")
        title.setFont(QFont("Cairo", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        # === شرح مختصر ===
        desc = QLabel(
            "\U0001f4e1 \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629 \u0628\u062a\u0646\u0642\u0644 \u0627\u0644\u0643\u0648\u062f \u0648\u0627\u0644\u062f\u0627\u062a\u0627\u0628\u064a\u0632 \u0628\u064a\u0646 \u0627\u0644\u0623\u062c\u0647\u0632\u0629 \u062a\u0644\u0642\u0627\u0626\u064a\u0627\u064b"
        )
        desc.setFont(QFont("Cairo", 10))
        desc.setAlignment(Qt.AlignCenter)
        desc.setObjectName("descLabel")
        layout.addWidget(desc)

        # === خيارات الأتمتة ===
        auto_group = QGroupBox("\u2699\ufe0f \u0627\u0644\u0623\u062a\u0645\u062a\u0629")
        auto_group.setFont(QFont("Cairo", 12, QFont.Bold))
        auto_group.setObjectName("optionsGroup")
        auto_layout = QVBoxLayout(auto_group)
        auto_layout.setSpacing(12)
        auto_layout.setContentsMargins(20, 20, 20, 20)

        # خيار 1: عند فتح البرنامج
        self._chk_startup = QCheckBox(
            "\U0001f504 \u0639\u0646\u062f \u0627\u0644\u0641\u062a\u062d: \u062c\u0644\u0628 \u0627\u0644\u062a\u062d\u062f\u064a\u062b\u0627\u062a + \u0627\u0633\u062a\u0639\u0627\u062f\u0629 \u0627\u0644\u062f\u0627\u062a\u0627\u0628\u064a\u0632  (git pull + restore)"
        )
        self._chk_startup.setFont(QFont("Cairo", 11))
        auto_layout.addWidget(self._chk_startup)

        # خيار 2: عند إغلاق البرنامج
        self._chk_exit = QCheckBox(
            "\U0001f6aa \u0639\u0646\u062f \u0627\u0644\u0625\u063a\u0644\u0627\u0642: \u0646\u0633\u062e \u0627\u0644\u062f\u0627\u062a\u0627\u0628\u064a\u0632 + \u0631\u0641\u0639 \u0627\u0644\u062a\u063a\u064a\u064a\u0631\u0627\u062a  (backup + git push)"
        )
        self._chk_exit.setFont(QFont("Cairo", 11))
        auto_layout.addWidget(self._chk_exit)

        # خيار 3: مزامنة دورية
        auto_row = QHBoxLayout()
        self._chk_auto = QCheckBox(
            "\u23f0 \u0645\u0632\u0627\u0645\u0646\u0629 \u062f\u0648\u0631\u064a\u0629 (backup + push) \u0643\u0644:"
        )
        self._chk_auto.setFont(QFont("Cairo", 11))
        auto_row.addWidget(self._chk_auto)

        self._spin_interval = QSpinBox()
        self._spin_interval.setRange(5, 240)
        self._spin_interval.setValue(30)
        self._spin_interval.setSuffix(" \u062f\u0642\u064a\u0642\u0629")
        self._spin_interval.setFont(QFont("Cairo", 11))
        self._spin_interval.setMinimumHeight(35)
        self._spin_interval.setMinimumWidth(120)
        self._spin_interval.setObjectName("intervalSpin")
        auto_row.addWidget(self._spin_interval)
        auto_row.addStretch()
        auto_layout.addLayout(auto_row)

        layout.addWidget(auto_group)

        # === أزرار المزامنة اليدوية ===
        sync_group = QGroupBox("\U0001f3ae \u0645\u0632\u0627\u0645\u0646\u0629 \u064a\u062f\u0648\u064a\u0629")
        sync_group.setFont(QFont("Cairo", 12, QFont.Bold))
        sync_group.setObjectName("optionsGroup")
        sync_layout = QHBoxLayout(sync_group)
        sync_layout.setSpacing(12)
        sync_layout.setContentsMargins(20, 20, 20, 20)

        # زرار Pull
        self._pull_btn = QPushButton("\u2b07\ufe0f \u062c\u0644\u0628 + \u0627\u0633\u062a\u0639\u0627\u062f\u0629")
        self._pull_btn.setFont(QFont("Cairo", 12, QFont.Bold))
        self._pull_btn.setMinimumHeight(45)
        self._pull_btn.setCursor(Qt.PointingHandCursor)
        self._pull_btn.setObjectName("pullBtn")
        self._pull_btn.setToolTip("git pull + database restore")
        self._pull_btn.clicked.connect(lambda: self._on_sync("pull"))
        sync_layout.addWidget(self._pull_btn)

        # زرار Push
        self._push_btn = QPushButton("\u2b06\ufe0f \u0646\u0633\u062e + \u0631\u0641\u0639")
        self._push_btn.setFont(QFont("Cairo", 12, QFont.Bold))
        self._push_btn.setMinimumHeight(45)
        self._push_btn.setCursor(Qt.PointingHandCursor)
        self._push_btn.setObjectName("pushBtn")
        self._push_btn.setToolTip("database backup + git push")
        self._push_btn.clicked.connect(lambda: self._on_sync("push"))
        sync_layout.addWidget(self._push_btn)

        # زرار Full
        self._full_btn = QPushButton("\U0001f504 \u0645\u0632\u0627\u0645\u0646\u0629 \u0643\u0627\u0645\u0644\u0629")
        self._full_btn.setFont(QFont("Cairo", 12, QFont.Bold))
        self._full_btn.setMinimumHeight(45)
        self._full_btn.setCursor(Qt.PointingHandCursor)
        self._full_btn.setObjectName("syncNowBtn")
        self._full_btn.setToolTip("pull + restore + backup + push")
        self._full_btn.clicked.connect(lambda: self._on_sync("full"))
        sync_layout.addWidget(self._full_btn)

        layout.addWidget(sync_group)

        # === آخر مزامنة ===
        self._status_label = QLabel("")
        self._status_label.setFont(QFont("Cairo", 11))
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

        # === سجل العمليات ===
        log_label = QLabel("\U0001f4cb \u0633\u062c\u0644 \u0627\u0644\u0639\u0645\u0644\u064a\u0627\u062a:")
        log_label.setFont(QFont("Cairo", 11))
        log_label.setObjectName("logLabel")
        layout.addWidget(log_label)

        self._log_area = QTextEdit()
        self._log_area.setReadOnly(True)
        self._log_area.setFont(QFont("Consolas", 10))
        self._log_area.setMinimumHeight(120)
        self._log_area.setObjectName("logArea")
        self._log_area.setPlaceholderText(
            "\u0627\u062e\u062a\u0631 \u0646\u0648\u0639 \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629 \u0644\u0639\u0631\u0636 \u0627\u0644\u0646\u062a\u0627\u0626\u062c..."
        )
        layout.addWidget(self._log_area)

        # === أزرار حفظ وإلغاء ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("\u0625\u0644\u063a\u0627\u0621")
        cancel_btn.setFont(QFont("Cairo", 12))
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("\U0001f4be \u062d\u0641\u0638 \u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a")
        save_btn.setFont(QFont("Cairo", 12, QFont.Bold))
        save_btn.setMinimumHeight(40)
        save_btn.setMinimumWidth(160)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _load_settings(self):
        """تحميل الإعدادات الحالية."""
        self._chk_startup.setChecked(self._config.get("sync_on_startup", True))
        self._chk_exit.setChecked(self._config.get("sync_on_exit", True))
        self._chk_auto.setChecked(self._config.get("auto_sync_enabled", False))
        self._spin_interval.setValue(self._config.get("auto_sync_interval_minutes", 30))

        last = self._config.get("last_sync_time", "")
        direction = self._config.get("last_sync_direction", "")
        if last:
            dir_text = {"pull": "\u2b07\ufe0f \u062c\u0644\u0628", "push": "\u2b06\ufe0f \u0631\u0641\u0639", "full": "\U0001f504 \u0643\u0627\u0645\u0644\u0629"}.get(direction, "")
            self._status_label.setText(f"\u0622\u062e\u0631 \u0645\u0632\u0627\u0645\u0646\u0629: {last} {dir_text} \u2705")
        else:
            self._status_label.setText("\u0644\u0645 \u062a\u062a\u0645 \u0645\u0632\u0627\u0645\u0646\u0629 \u0628\u0639\u062f")

    def _on_save(self):
        """حفظ الإعدادات."""
        self._config["sync_on_startup"] = self._chk_startup.isChecked()
        self._config["sync_on_exit"] = self._chk_exit.isChecked()
        self._config["auto_sync_enabled"] = self._chk_auto.isChecked()
        self._config["auto_sync_interval_minutes"] = self._spin_interval.value()
        save_sync_config(self._config)
        self.accept()

    def _on_sync(self, mode: str):
        """تشغيل المزامنة."""
        if self._worker and self._worker.isRunning():
            return

        # تعطيل الأزرار
        self._pull_btn.setEnabled(False)
        self._push_btn.setEnabled(False)
        self._full_btn.setEnabled(False)

        mode_names = {"pull": "\u062c\u0644\u0628 + \u0627\u0633\u062a\u0639\u0627\u062f\u0629", "push": "\u0646\u0633\u062e + \u0631\u0641\u0639", "full": "\u0645\u0632\u0627\u0645\u0646\u0629 \u0643\u0627\u0645\u0644\u0629"}
        self._log_area.clear()
        self._log_area.append(f"\u23f3 \u062c\u0627\u0631\u064a: {mode_names.get(mode, mode)}...\n")

        self._current_mode = mode
        self._worker = SyncWorker(mode=mode)
        self._worker.finished.connect(self._on_sync_finished)
        self._worker.start()

    def _on_sync_finished(self, success, logs):
        """بعد انتهاء المزامنة."""
        from datetime import datetime

        for log in logs:
            self._log_area.append(f"  {log}")

        self._log_area.append("")
        if success:
            self._log_area.append("\u2705 \u062a\u0645\u062a \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629 \u0628\u0646\u062c\u0627\u062d!")
        else:
            self._log_area.append("\u26a0\ufe0f \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629 \u0644\u0645 \u062a\u0643\u062a\u0645\u0644 \u0628\u0646\u062c\u0627\u062d")

        # تحديث وقت آخر مزامنة
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._config["last_sync_time"] = now
        self._config["last_sync_direction"] = getattr(self, "_current_mode", "")
        save_sync_config(self._config)

        mode = getattr(self, "_current_mode", "")
        dir_text = {"pull": "\u2b07\ufe0f \u062c\u0644\u0628", "push": "\u2b06\ufe0f \u0631\u0641\u0639", "full": "\U0001f504 \u0643\u0627\u0645\u0644\u0629"}.get(mode, "")
        self._status_label.setText(f"\u0622\u062e\u0631 \u0645\u0632\u0627\u0645\u0646\u0629: {now} {dir_text} \u2705")

        # تفعيل الأزرار
        self._pull_btn.setEnabled(True)
        self._push_btn.setEnabled(True)
        self._full_btn.setEnabled(True)

    def _apply_theme(self):
        """تطبيق الثيم."""
        theme = get_current_theme()

        if theme == "dark":
            self.setStyleSheet("""
                QDialog { background-color: #0f172a; }
                QLabel { color: #f1f5f9; background: transparent; }
                QLabel#dialogTitle { color: #38bdf8; }
                QLabel#descLabel { color: #64748b; }
                QLabel#statusLabel { color: #94a3b8; }
                QLabel#logLabel { color: #94a3b8; }

                QGroupBox {
                    color: #06b6d4;
                    border: 1px solid #334155;
                    border-radius: 10px;
                    margin-top: 10px;
                    padding-top: 15px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 15px;
                    padding: 0 8px;
                }

                QCheckBox { color: #f1f5f9; spacing: 10px; }
                QCheckBox::indicator {
                    width: 22px; height: 22px;
                    border: 2px solid #475569;
                    border-radius: 4px;
                    background: #1e293b;
                }
                QCheckBox::indicator:checked {
                    background: #06b6d4;
                    border-color: #06b6d4;
                }
                QCheckBox::indicator:hover { border-color: #06b6d4; }

                QSpinBox {
                    background: #1e293b; color: #f1f5f9;
                    border: 2px solid #334155; border-radius: 6px;
                    padding: 5px 10px;
                }
                QSpinBox:focus { border-color: #06b6d4; }

                QPushButton#pullBtn {
                    background: #0d9488; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#pullBtn:hover { background: #14b8a6; }
                QPushButton#pullBtn:disabled { background: #334155; color: #64748b; }

                QPushButton#pushBtn {
                    background: #7c3aed; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#pushBtn:hover { background: #8b5cf6; }
                QPushButton#pushBtn:disabled { background: #334155; color: #64748b; }

                QPushButton#syncNowBtn {
                    background: #0891b2; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#syncNowBtn:hover { background: #06b6d4; }
                QPushButton#syncNowBtn:disabled { background: #334155; color: #64748b; }

                QPushButton#saveBtn {
                    background: #10b981; color: #ffffff;
                    border: none; border-radius: 8px;
                    padding: 8px 20px;
                }
                QPushButton#saveBtn:hover { background: #059669; }

                QPushButton#cancelBtn {
                    background: #334155; color: #f1f5f9;
                    border: none; border-radius: 8px;
                    padding: 8px 20px;
                }
                QPushButton#cancelBtn:hover { background: #475569; }

                QTextEdit#logArea {
                    background: #1e293b; color: #e2e8f0;
                    border: 1px solid #334155; border-radius: 8px;
                    padding: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background-color: #f8fafc; }
                QLabel { color: #1e293b; background: transparent; }
                QLabel#dialogTitle { color: #0891b2; }
                QLabel#descLabel { color: #94a3b8; }
                QLabel#statusLabel { color: #64748b; }
                QLabel#logLabel { color: #64748b; }

                QGroupBox {
                    color: #0891b2;
                    border: 1px solid #e2e8f0;
                    border-radius: 10px;
                    margin-top: 10px;
                    padding-top: 15px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 15px;
                    padding: 0 8px;
                }

                QCheckBox { color: #1e293b; spacing: 10px; }
                QCheckBox::indicator {
                    width: 22px; height: 22px;
                    border: 2px solid #cbd5e1;
                    border-radius: 4px;
                    background: #ffffff;
                }
                QCheckBox::indicator:checked {
                    background: #0891b2;
                    border-color: #0891b2;
                }

                QSpinBox {
                    background: #ffffff; color: #1e293b;
                    border: 2px solid #e2e8f0; border-radius: 6px;
                    padding: 5px 10px;
                }

                QPushButton#pullBtn {
                    background: #0d9488; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#pullBtn:hover { background: #14b8a6; }
                QPushButton#pullBtn:disabled { background: #e2e8f0; color: #94a3b8; }

                QPushButton#pushBtn {
                    background: #7c3aed; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#pushBtn:hover { background: #8b5cf6; }
                QPushButton#pushBtn:disabled { background: #e2e8f0; color: #94a3b8; }

                QPushButton#syncNowBtn {
                    background: #0891b2; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#syncNowBtn:hover { background: #06b6d4; }
                QPushButton#syncNowBtn:disabled { background: #e2e8f0; color: #94a3b8; }

                QPushButton#saveBtn {
                    background: #10b981; color: #ffffff;
                    border: none; border-radius: 8px;
                    padding: 8px 20px;
                }
                QPushButton#cancelBtn {
                    background: #e2e8f0; color: #1e293b;
                    border: none; border-radius: 8px;
                    padding: 8px 20px;
                }

                QTextEdit#logArea {
                    background: #ffffff; color: #334155;
                    border: 1px solid #e2e8f0; border-radius: 8px;
                    padding: 10px;
                }
            """)
