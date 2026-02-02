# -*- coding: utf-8 -*-
"""Progress Dialog v3 - Progress Bar موحد لكل البرنامج"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
import time


class ProgressDialog(QDialog):
    cancelled = pyqtSignal()
    
    BAR_COLOR = "#00E676"
    BAR_BG = "#424242"
    TEXT_COLOR = "#FFFFFF"
    BG_COLOR = "#2D2D2D"
    
    def __init__(self, title: str = "جاري التحميل...", parent=None,
                 show_cancel: bool = False, show_time: bool = True,
                 min_width: int = 400):
        super().__init__(parent)
        
        self.setWindowTitle("INTEGRA")
        self.setMinimumWidth(min_width)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        self.setModal(True)
        
        self._start_time = time.time()
        self._show_time = show_time
        self._last_percent = 0
        
        self._setup_ui(title, show_cancel)
        self._apply_style()
    
    def _setup_ui(self, title: str, show_cancel: bool):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)
        
        self._title_label = QLabel(title)
        self._title_label.setAlignment(Qt.AlignCenter)
        font = QFont("Cairo", 12, QFont.Bold)
        self._title_label.setFont(font)
        layout.addWidget(self._title_label)
        
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")
        self._progress_bar.setMinimumHeight(25)
        layout.addWidget(self._progress_bar)
        
        info_layout = QHBoxLayout()
        self._message_label = QLabel("")
        self._message_label.setAlignment(Qt.AlignLeft)
        info_layout.addWidget(self._message_label)
        info_layout.addStretch()
        self._time_label = QLabel("")
        self._time_label.setAlignment(Qt.AlignRight)
        info_layout.addWidget(self._time_label)
        layout.addLayout(info_layout)
        
        if show_cancel:
            self._cancel_btn = QPushButton("إلغاء")
            self._cancel_btn.clicked.connect(self._on_cancel)
            layout.addWidget(self._cancel_btn, alignment=Qt.AlignCenter)
        else:
            self._cancel_btn = None
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {self.BG_COLOR}; }}
            QLabel {{ color: {self.TEXT_COLOR}; }}
            QProgressBar {{
                border: none; border-radius: 12px;
                background-color: {self.BAR_BG};
                text-align: center; color: {self.TEXT_COLOR};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.BAR_COLOR}, stop:1 #69F0AE);
            }}
            QPushButton {{
                background-color: #616161; color: white;
                border: none; border-radius: 5px;
                padding: 8px 20px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #757575; }}
        """)
    
    def set_progress(self, percent: int, message: str = ""):
        percent = max(0, min(100, percent))
        self._progress_bar.setValue(percent)
        
        if message:
            self._message_label.setText(message)
        
        if self._show_time and percent > 0:
            elapsed = time.time() - self._start_time
            if percent < 100:
                estimated_total = elapsed / (percent / 100)
                remaining = estimated_total - elapsed
                if remaining > 0:
                    self._time_label.setText(f"الوقت المتبقي: {remaining:.0f} ثانية")
                else:
                    self._time_label.setText("")
            else:
                self._time_label.setText(f"انتهى في {elapsed:.1f} ثانية")
        
        self._last_percent = percent
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
    
    def set_title(self, title: str):
        self._title_label.setText(title)
    
    def set_message(self, message: str):
        self._message_label.setText(message)
    
    def _on_cancel(self):
        self.cancelled.emit()
        self.close()
    
    def finish_success(self, message: str = "تم بنجاح!"):
        self.set_progress(100, message)
        QTimer.singleShot(500, self.accept)
    
    def finish_error(self, message: str = "حدث خطأ"):
        self._title_label.setText("خطأ: " + message)
        self._progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")
        if self._cancel_btn:
            self._cancel_btn.setText("إغلاق")
        else:
            QTimer.singleShot(2000, self.reject)


class QuickProgress:
    def __init__(self, title: str, parent=None):
        self.dialog = ProgressDialog(title, parent)
    
    def __enter__(self):
        self.dialog.show()
        return self.dialog
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.dialog.finish_success()
        else:
            self.dialog.finish_error(str(exc_val))
        return False
