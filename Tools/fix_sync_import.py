# Tools/fix_sync_import.py
"""
═══════════════════════════════════════════════════════════════════
  INTEGRA - إصلاح خطأ SyncWorker Import
═══════════════════════════════════════════════════════════════════
  cd /d D:\Projects\Integra
  python Tools\fix_sync_import.py
═══════════════════════════════════════════════════════════════════

  المشكلة: install_sync_v3.py حدّث core/sync/ لكن ما حدّثش
           sync_settings_dialog.py - فالملف القديم لسه بيستورد
           SyncWorker اللي اتشال.

  الحل:    1) تحديث sync_settings_dialog.py للإصدار v3
           2) فحص كل ملفات المشروع للتأكد مفيش import تاني لـ SyncWorker
═══════════════════════════════════════════════════════════════════
"""

import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent

print()
print("=" * 65)
print("  INTEGRA - إصلاح خطأ SyncWorker Import")
print("=" * 65)
print(f"  المسار: {PROJECT_ROOT}")
print(f"  التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 65)

# ═══════════════════════════════════════════════════════════════
# الخطوة 1: البحث عن الملف القديم
# ═══════════════════════════════════════════════════════════════

print("\n[1/3] البحث عن sync_settings_dialog.py القديم...")

# المسارات المحتملة للملف
possible_paths = [
    PROJECT_ROOT / "ui" / "dialogs" / "sync_settings" / "sync_settings_dialog.py",
    PROJECT_ROOT / "ui" / "dialogs" / "sync_settings_dialog.py",
    PROJECT_ROOT / "sync_settings_dialog.py",
]

found_path = None
for p in possible_paths:
    if p.exists():
        found_path = p
        # فحص هل الملف فيه SyncWorker
        content = p.read_text(encoding="utf-8")
        if "SyncWorker" in content:
            print(f"  ⚠️  وُجد الملف القديم: {p.relative_to(PROJECT_ROOT)}")
            print(f"      يحتوي على import لـ SyncWorker ← هذا سبب الخطأ!")
        else:
            print(f"  ✅ وُجد الملف: {p.relative_to(PROJECT_ROOT)}")
            print(f"      لا يحتوي على SyncWorker (قد يكون محدّث)")
        break

if found_path is None:
    # نبحث في كل المشروع
    for p in PROJECT_ROOT.rglob("sync_settings_dialog.py"):
        if "__pycache__" not in str(p):
            found_path = p
            content = p.read_text(encoding="utf-8")
            has_worker = "SyncWorker" in content
            print(f"  {'⚠️' if has_worker else '✅'} وُجد: {p.relative_to(PROJECT_ROOT)}")
            break

if found_path is None:
    print("  ❌ الملف غير موجود! سيتم إنشاؤه...")
    # نستخدم المسار الأول كمسار افتراضي
    found_path = possible_paths[0]

# ═══════════════════════════════════════════════════════════════
# الخطوة 2: كتابة الملف المحدّث (v3)
# ═══════════════════════════════════════════════════════════════

print("\n[2/3] تحديث sync_settings_dialog.py إلى v3...")

# التأكد من وجود المجلد
found_path.parent.mkdir(parents=True, exist_ok=True)

# النسخة الجديدة المتوافقة مع Sync v3
NEW_DIALOG = r'''# -*- coding: utf-8 -*-
"""
Sync Settings Dialog - v3
=========================
شاشة إعدادات المزامنة - متوافقة مع Sync System v3

التغييرات عن v2:
- DB تلقائي، Git يدوي فقط
- Backups متعددة بتسلسل وتاريخ
- استعادة backup محدد
- الدوري بالساعات (≥ 1 ساعة)
"""

from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QSpinBox, QFrame,
    QTextEdit, QGroupBox, QListWidget, QListWidgetItem,
    QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.themes import get_current_theme
from core.sync import get_sync_manager, load_sync_config, save_sync_config


class SyncSettingsDialog(QDialog):
    """شاشة إعدادات المزامنة v3."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ إعدادات المزامنة")
        self.setMinimumSize(600, 650)

        self._sync = get_sync_manager()
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
        title = QLabel("⚙️ إعدادات المزامنة")
        title.setFont(QFont("Cairo", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        # ══════════════════════════════════════════
        # 📊 قاعدة البيانات
        # ══════════════════════════════════════════
        db_group = QGroupBox("📊 قاعدة البيانات")
        db_group.setFont(QFont("Cairo", 12, QFont.Bold))
        db_group.setObjectName("optionsGroup")
        db_layout = QVBoxLayout(db_group)
        db_layout.setSpacing(12)
        db_layout.setContentsMargins(20, 20, 20, 20)

        # مزامنة عند الفتح
        self._chk_startup = QCheckBox(
            "🔄 مزامنة عند فتح البرنامج"
        )
        self._chk_startup.setFont(QFont("Cairo", 11))
        db_layout.addWidget(self._chk_startup)

        # مزامنة دورية
        auto_row = QHBoxLayout()
        self._chk_auto = QCheckBox("⏰ مزامنة دورية كل:")
        self._chk_auto.setFont(QFont("Cairo", 11))
        auto_row.addWidget(self._chk_auto)

        self._spin_interval = QSpinBox()
        self._spin_interval.setRange(1, 24)
        self._spin_interval.setValue(2)
        self._spin_interval.setSuffix(" ساعة")
        self._spin_interval.setFont(QFont("Cairo", 11))
        self._spin_interval.setMinimumHeight(35)
        self._spin_interval.setMinimumWidth(110)
        self._spin_interval.setObjectName("intervalSpin")
        auto_row.addWidget(self._spin_interval)
        auto_row.addStretch()
        db_layout.addLayout(auto_row)

        # زرار مزامنة الآن
        self._db_sync_btn = QPushButton("🔄 مزامنة الآن")
        self._db_sync_btn.setFont(QFont("Cairo", 12, QFont.Bold))
        self._db_sync_btn.setMinimumHeight(40)
        self._db_sync_btn.setCursor(Qt.PointingHandCursor)
        self._db_sync_btn.setObjectName("syncNowBtn")
        self._db_sync_btn.clicked.connect(self._on_db_sync)
        db_layout.addWidget(self._db_sync_btn)

        layout.addWidget(db_group)

        # ══════════════════════════════════════════
        # 📂 النسخ الاحتياطية
        # ══════════════════════════════════════════
        backup_group = QGroupBox("📂 النسخ الاحتياطية")
        backup_group.setFont(QFont("Cairo", 12, QFont.Bold))
        backup_group.setObjectName("optionsGroup")
        backup_layout = QVBoxLayout(backup_group)
        backup_layout.setSpacing(10)
        backup_layout.setContentsMargins(20, 20, 20, 20)

        # آخر نسخة
        self._backup_info_label = QLabel("آخر نسخة: جاري التحقق...")
        self._backup_info_label.setFont(QFont("Cairo", 11))
        self._backup_info_label.setObjectName("statusLabel")
        backup_layout.addWidget(self._backup_info_label)

        # زرار استعادة نسخة سابقة
        self._restore_btn = QPushButton("📥 استعادة نسخة سابقة...")
        self._restore_btn.setFont(QFont("Cairo", 11, QFont.Bold))
        self._restore_btn.setMinimumHeight(38)
        self._restore_btn.setCursor(Qt.PointingHandCursor)
        self._restore_btn.setObjectName("pullBtn")
        self._restore_btn.clicked.connect(self._on_restore_backup)
        backup_layout.addWidget(self._restore_btn)

        layout.addWidget(backup_group)

        # ══════════════════════════════════════════
        # 💻 تحديثات التطوير (Git)
        # ══════════════════════════════════════════
        git_group = QGroupBox("💻 تحديثات التطوير (Git)")
        git_group.setFont(QFont("Cairo", 12, QFont.Bold))
        git_group.setObjectName("optionsGroup")
        git_layout = QHBoxLayout(git_group)
        git_layout.setSpacing(12)
        git_layout.setContentsMargins(20, 20, 20, 20)

        # جلب التحديثات
        self._git_pull_btn = QPushButton("⬇️ جلب التحديثات")
        self._git_pull_btn.setFont(QFont("Cairo", 12, QFont.Bold))
        self._git_pull_btn.setMinimumHeight(45)
        self._git_pull_btn.setCursor(Qt.PointingHandCursor)
        self._git_pull_btn.setObjectName("pullBtn")
        self._git_pull_btn.clicked.connect(self._on_git_pull)
        git_layout.addWidget(self._git_pull_btn)

        # رفع التحديثات
        self._git_push_btn = QPushButton("⬆️ رفع التحديثات")
        self._git_push_btn.setFont(QFont("Cairo", 12, QFont.Bold))
        self._git_push_btn.setMinimumHeight(45)
        self._git_push_btn.setCursor(Qt.PointingHandCursor)
        self._git_push_btn.setObjectName("pushBtn")
        self._git_push_btn.clicked.connect(self._on_git_push)
        git_layout.addWidget(self._git_push_btn)

        layout.addWidget(git_group)

        # === آخر مزامنة + سجل ===
        self._status_label = QLabel("")
        self._status_label.setFont(QFont("Cairo", 11))
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

        # سجل العمليات
        log_label = QLabel("📋 سجل العمليات:")
        log_label.setFont(QFont("Cairo", 11))
        log_label.setObjectName("logLabel")
        layout.addWidget(log_label)

        self._log_area = QTextEdit()
        self._log_area.setReadOnly(True)
        self._log_area.setFont(QFont("Consolas", 10))
        self._log_area.setMinimumHeight(100)
        self._log_area.setMaximumHeight(140)
        self._log_area.setObjectName("logArea")
        self._log_area.setPlaceholderText("اختر عملية لعرض النتائج...")
        layout.addWidget(self._log_area)

        # === أزرار حفظ وإلغاء ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setFont(QFont("Cairo", 12))
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 حفظ الإعدادات")
        save_btn.setFont(QFont("Cairo", 12, QFont.Bold))
        save_btn.setMinimumHeight(40)
        save_btn.setMinimumWidth(160)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    # ═══════════════════════════════════════════════════════════
    # تحميل وحفظ الإعدادات
    # ═══════════════════════════════════════════════════════════

    def _load_settings(self):
        """تحميل الإعدادات من الملف."""
        self._chk_startup.setChecked(
            self._config.get("sync_on_startup", True)
        )
        self._chk_auto.setChecked(
            self._config.get("auto_sync_enabled", False)
        )
        self._spin_interval.setValue(
            self._config.get("auto_sync_interval_hours", 2)
        )

        # آخر مزامنة
        last_sync = self._config.get("last_sync_time", "")
        if last_sync:
            self._status_label.setText(f"آخر مزامنة: {last_sync}")
        else:
            self._status_label.setText("لم تتم مزامنة بعد")

        # معلومات آخر backup
        self._update_backup_info()

    def _update_backup_info(self):
        """تحديث معلومات آخر backup."""
        latest = self._sync.get_latest_backup()
        if latest:
            self._backup_info_label.setText(
                f"آخر نسخة: {latest.formatted_time} ({latest.formatted_size})"
            )
        else:
            self._backup_info_label.setText("لا توجد نسخ احتياطية")

    def _on_save(self):
        """حفظ الإعدادات."""
        self._sync.update_config(
            sync_on_startup=self._chk_startup.isChecked(),
            auto_sync_enabled=self._chk_auto.isChecked(),
            auto_sync_interval_hours=self._spin_interval.value(),
        )

        self._log_area.append("✅ تم حفظ الإعدادات")
        self._status_label.setText("✅ تم حفظ الإعدادات")

    # ═══════════════════════════════════════════════════════════
    # عمليات المزامنة
    # ═══════════════════════════════════════════════════════════

    def _set_buttons_enabled(self, enabled: bool):
        """تفعيل/تعطيل كل الأزرار."""
        self._db_sync_btn.setEnabled(enabled)
        self._git_pull_btn.setEnabled(enabled)
        self._git_push_btn.setEnabled(enabled)
        self._restore_btn.setEnabled(enabled)

    def _on_db_sync(self):
        """مزامنة قاعدة البيانات."""
        self._set_buttons_enabled(False)
        self._log_area.clear()
        self._log_area.append("🔄 جاري مزامنة قاعدة البيانات...")

        def on_progress(percent, message):
            self._status_label.setText(f"{message} ({percent}%)")

        def on_finished(success, summary):
            if success:
                self._log_area.append(f"✅ {summary}")
            else:
                self._log_area.append(f"❌ {summary}")

            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._status_label.setText(f"آخر مزامنة: {now}")
            self._update_backup_info()
            self._set_buttons_enabled(True)

        self._sync.sync_database(
            on_progress=on_progress,
            on_finished=on_finished
        )

    def _on_git_pull(self):
        """جلب تحديثات الكود."""
        self._set_buttons_enabled(False)
        self._log_area.clear()
        self._log_area.append("⬇️ جاري جلب تحديثات الكود...")

        def on_progress(percent, message):
            self._status_label.setText(f"{message} ({percent}%)")

        def on_finished(success, summary):
            if success:
                self._log_area.append(f"✅ {summary}")
            else:
                self._log_area.append(f"❌ {summary}")
            self._set_buttons_enabled(True)

        self._sync.git_pull(
            on_progress=on_progress,
            on_finished=on_finished
        )

    def _on_git_push(self):
        """رفع تحديثات الكود."""
        self._set_buttons_enabled(False)
        self._log_area.clear()
        self._log_area.append("⬆️ جاري رفع تحديثات الكود...")

        def on_progress(percent, message):
            self._status_label.setText(f"{message} ({percent}%)")

        def on_finished(success, summary):
            if success:
                self._log_area.append(f"✅ {summary}")
            else:
                self._log_area.append(f"❌ {summary}")
            self._set_buttons_enabled(True)

        self._sync.git_push(
            on_progress=on_progress,
            on_finished=on_finished
        )

    def _on_restore_backup(self):
        """استعادة نسخة احتياطية سابقة."""
        backups = self._sync.list_backups()

        if not backups:
            QMessageBox.information(
                self, "النسخ الاحتياطية",
                "لا توجد نسخ احتياطية متاحة."
            )
            return

        # عرض قائمة الـ backups في dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("📥 استعادة نسخة سابقة")
        dialog.setMinimumSize(450, 350)

        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.setContentsMargins(20, 20, 20, 20)
        dlg_layout.setSpacing(12)

        dlg_label = QLabel("اختر النسخة المراد استعادتها:")
        dlg_label.setFont(QFont("Cairo", 12))
        dlg_layout.addWidget(dlg_label)

        backup_list = QListWidget()
        backup_list.setFont(QFont("Consolas", 11))
        for backup in backups:
            item = QListWidgetItem(
                f"{backup.formatted_time}  |  {backup.formatted_size}"
            )
            item.setData(Qt.UserRole, backup.filename)
            backup_list.addItem(item)
        dlg_layout.addWidget(backup_list)

        # أزرار
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setFont(QFont("Cairo", 11))
        cancel_btn.setMinimumHeight(35)
        cancel_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(cancel_btn)

        restore_btn = QPushButton("📥 استعادة")
        restore_btn.setFont(QFont("Cairo", 11, QFont.Bold))
        restore_btn.setMinimumHeight(35)
        restore_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(restore_btn)

        dlg_layout.addLayout(btn_row)

        # تطبيق ثيم بسيط
        theme = get_current_theme()
        if theme == "dark":
            dialog.setStyleSheet("""
                QDialog { background-color: #1e293b; }
                QLabel { color: #f1f5f9; }
                QListWidget {
                    background: #0f172a; color: #e2e8f0;
                    border: 1px solid #334155; border-radius: 8px;
                    padding: 5px;
                }
                QListWidget::item { padding: 8px; border-radius: 4px; }
                QListWidget::item:selected { background: #0891b2; }
                QPushButton {
                    background: #334155; color: #f1f5f9;
                    border: none; border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton:hover { background: #475569; }
            """)
        else:
            dialog.setStyleSheet("""
                QDialog { background-color: #f8fafc; }
                QLabel { color: #1e293b; }
                QListWidget {
                    background: #ffffff; color: #334155;
                    border: 1px solid #e2e8f0; border-radius: 8px;
                    padding: 5px;
                }
                QListWidget::item { padding: 8px; border-radius: 4px; }
                QListWidget::item:selected { background: #0891b2; color: white; }
                QPushButton {
                    background: #e2e8f0; color: #1e293b;
                    border: none; border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton:hover { background: #cbd5e1; }
            """)

        if dialog.exec_() != QDialog.Accepted:
            return

        selected = backup_list.currentItem()
        if not selected:
            return

        filename = selected.data(Qt.UserRole)
        backup_info = self._sync.backup_manager.get_backup_by_filename(filename)
        if not backup_info:
            return

        # تأكيد
        reply = QMessageBox.warning(
            self, "تأكيد الاستعادة",
            f"هل أنت متأكد؟\n"
            f"سيتم استبدال البيانات الحالية بنسخة:\n"
            f"{backup_info.formatted_time} ({backup_info.formatted_size})",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # تنفيذ الاستعادة
        self._log_area.clear()
        self._log_area.append(f"📥 جاري استعادة نسخة {backup_info.formatted_time}...")
        self._set_buttons_enabled(False)

        def on_progress(percent, message):
            self._status_label.setText(f"{message} ({percent}%)")

        success, _ = self._sync.restore_backup(backup_info, on_progress)

        if success:
            self._log_area.append("✅ تمت الاستعادة بنجاح!")
            self._status_label.setText("✅ تمت الاستعادة")
        else:
            self._log_area.append("❌ فشلت الاستعادة")
            self._status_label.setText("❌ فشلت الاستعادة")

        self._set_buttons_enabled(True)

    # ═══════════════════════════════════════════════════════════
    # الثيم
    # ═══════════════════════════════════════════════════════════

    def _apply_theme(self):
        """تطبيق الثيم."""
        theme = get_current_theme()

        if theme == "dark":
            self.setStyleSheet("""
                QDialog { background-color: #0f172a; }
                QLabel { color: #f1f5f9; background: transparent; }
                QLabel#dialogTitle { color: #38bdf8; }
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

                QPushButton#syncNowBtn {
                    background: #0891b2; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#syncNowBtn:hover { background: #06b6d4; }
                QPushButton#syncNowBtn:disabled { background: #334155; color: #64748b; }

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

                QPushButton#syncNowBtn {
                    background: #0891b2; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#syncNowBtn:hover { background: #06b6d4; }
                QPushButton#syncNowBtn:disabled { background: #e2e8f0; color: #94a3b8; }

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
'''

# نعمل backup للملف القديم
if found_path.exists():
    backup_name = found_path.with_suffix(".py.old_v2")
    if not backup_name.exists():
        import shutil
        shutil.copy(str(found_path), str(backup_name))
        print(f"  📦 نسخة احتياطية: {backup_name.name}")

# كتابة الملف الجديد
found_path.write_text(NEW_DIALOG.strip(), encoding="utf-8")
print(f"  ✅ تم تحديث: {found_path.relative_to(PROJECT_ROOT)}")

# التأكد من وجود __init__.py
init_file = found_path.parent / "__init__.py"
if not init_file.exists():
    init_file.write_text(
        "from .sync_settings_dialog import SyncSettingsDialog\n",
        encoding="utf-8"
    )
    print(f"  ✅ تم إنشاء: {init_file.relative_to(PROJECT_ROOT)}")

# ═══════════════════════════════════════════════════════════════
# الخطوة 3: فحص كل المشروع لأي import SyncWorker متبقي
# ═══════════════════════════════════════════════════════════════

print("\n[3/3] فحص المشروع لأي SyncWorker imports متبقية...")

problems_found = 0
skip_dirs = {"__pycache__", ".git", "venv", "node_modules", ".old_v2"}

for py_file in PROJECT_ROOT.rglob("*.py"):
    # تخطي المجلدات غير المهمة
    if any(skip in py_file.parts for skip in skip_dirs):
        continue
    # تخطي هذا السكريبت نفسه
    if py_file.name == "fix_sync_import.py":
        continue

    try:
        content = py_file.read_text(encoding="utf-8")
        if "SyncWorker" in content:
            # التأكد إنه import وليس تعريف الكلاس
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if "SyncWorker" in stripped and "import" in stripped:
                    if "from core.sync import" in stripped or "from .sync" in stripped:
                        # هذا import - نتأكد هل هو في __init__.py أو sync_manager
                        rel_path = py_file.relative_to(PROJECT_ROOT)
                        # لو في sync_manager.py ده طبيعي (تعريف داخلي)
                        if py_file.name == "sync_manager.py":
                            continue
                        print(f"  ⚠️  {rel_path} سطر {i}: {stripped}")
                        problems_found += 1
    except (UnicodeDecodeError, PermissionError):
        continue

# فحص __pycache__ القديمة
print("\n  🧹 تنظيف __pycache__...")
cache_dirs = list(PROJECT_ROOT.rglob("__pycache__"))
sync_caches = [d for d in cache_dirs if "sync" in str(d).lower()]
cleaned = 0
for cache_dir in sync_caches:
    for cached_file in cache_dir.glob("*.pyc"):
        cached_file.unlink()
        cleaned += 1
    for cached_file in cache_dir.glob("*.pyo"):
        cached_file.unlink()
        cleaned += 1

if cleaned:
    print(f"     حُذف {cleaned} ملف cache من مجلدات sync")
else:
    print("     لا توجد ملفات cache للحذف")

# ═══════════════════════════════════════════════════════════════
# النتيجة النهائية
# ═══════════════════════════════════════════════════════════════

print()
print("=" * 65)
if problems_found == 0:
    print("  ✅ تم الإصلاح بنجاح! لا توجد مشاكل متبقية")
else:
    print(f"  ⚠️  تم تحديث الملف الرئيسي لكن وُجدت {problems_found} مشاكل إضافية")
    print("      راجع التفاصيل أعلاه")
print("=" * 65)
print()
print("  ما تم:")
print(f"  1. تحديث sync_settings_dialog.py → v3")
print(f"  2. فحص كل ملفات المشروع ← {'نظيف ✅' if problems_found == 0 else f'{problems_found} مشاكل ⚠️'}")
print(f"  3. تنظيف __pycache__ للـ sync ← {cleaned} ملف")
print()
print("  الخطوة التالية:")
print("  python main.py")
print("=" * 65)
