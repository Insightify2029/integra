# -*- coding: utf-8 -*-
"""Progress Dialog v3 - Unified progress bar for the application.
Styling handled by centralized theme system."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from core.themes import (
    get_current_palette, get_font,
    FONT_SIZE_BODY, FONT_WEIGHT_BOLD
)
import time


class ProgressDialog(QDialog):
    cancelled = pyqtSignal()

    def __init__(self, title: str = "\u062c\u0627\u0631\u064a \u0627\u0644\u062a\u062d\u0645\u064a\u0644...", parent=None,
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
        self._processing_events = False

        self._setup_ui(title, show_cancel)
        # App-level QSS handles QDialog, QLabel, QProgressBar, QPushButton styling

    def _setup_ui(self, title: str, show_cancel: bool):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)

        self._title_label = QLabel(title)
        self._title_label.setAlignment(Qt.AlignCenter)
        self._title_label.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))
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
            self._cancel_btn = QPushButton("\u0625\u0644\u063a\u0627\u0621")
            self._cancel_btn.setProperty("cssClass", "secondary")
            self._cancel_btn.clicked.connect(self._on_cancel)
            layout.addWidget(self._cancel_btn, alignment=Qt.AlignCenter)
        else:
            self._cancel_btn = None

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
                    self._time_label.setText(f"\u0627\u0644\u0648\u0642\u062a \u0627\u0644\u0645\u062a\u0628\u0642\u064a: {remaining:.0f} \u062b\u0627\u0646\u064a\u0629")
                else:
                    self._time_label.setText("")
            else:
                self._time_label.setText(f"\u0627\u0646\u062a\u0647\u0649 \u0641\u064a {elapsed:.1f} \u062b\u0627\u0646\u064a\u0629")

        self._last_percent = percent
        if not self._processing_events:
            self._processing_events = True
            try:
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
            finally:
                self._processing_events = False

    def set_title(self, title: str):
        self._title_label.setText(title)

    def set_message(self, message: str):
        self._message_label.setText(message)

    def _on_cancel(self):
        self.cancelled.emit()
        self.close()

    def finish_success(self, message: str = "\u062a\u0645 \u0628\u0646\u062c\u0627\u062d!"):
        self.set_progress(100, message)
        QTimer.singleShot(500, self.accept)

    def finish_error(self, message: str = "\u062d\u062f\u062b \u062e\u0637\u0623"):
        palette = get_current_palette()
        self._title_label.setText("\u062e\u0637\u0623: " + message)
        self._progress_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {palette['danger']}; }}"
        )
        if self._cancel_btn:
            self._cancel_btn.setText("\u0625\u063a\u0644\u0627\u0642")
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
