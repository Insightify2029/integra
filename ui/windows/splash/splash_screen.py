"""
INTEGRA Professional Splash Screen
====================================
Fast, elegant splash screen shown during application startup.
"""

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5.QtGui import (
    QPainter, QColor, QLinearGradient,
    QPainterPath, QPen
)

from core.config.app import APP_VERSION
from core.themes import (
    get_current_palette, get_font,
    FONT_SIZE_LOGO, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY,
    FONT_SIZE_SMALL, FONT_SIZE_TINY, FONT_WEIGHT_BOLD
)


class IntegraSplashScreen(QWidget):
    """Professional splash screen with progress indication."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.SplashScreen
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(620, 400)

        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            int((screen.width() - 620) / 2),
            int((screen.height() - 400) / 2)
        )

        self._progress = 0
        self._status = ""
        self._dots_count = 0

        # Dots animation timer
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self._animate_dots)
        self._dot_timer.start(400)

    def _animate_dots(self):
        """Animate loading dots."""
        self._dots_count = (self._dots_count + 1) % 4
        self.update()

    def paintEvent(self, event):
        """Paint the splash screen."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        rect = QRectF(self.rect())

        palette = get_current_palette()

        # === Background with gradient ===
        grad = QLinearGradient(0, 0, 0, rect.height())
        grad.setColorAt(0.0, QColor(palette['bg_main']))
        grad.setColorAt(0.5, QColor(palette['bg_card']))
        grad.setColorAt(1.0, QColor(palette['bg_main']))

        path = QPainterPath()
        path.addRoundedRect(rect, 18, 18)
        p.fillPath(path, grad)

        # === Subtle border ===
        primary_color = QColor(palette['primary'])
        primary_color.setAlpha(60)
        p.setPen(QPen(primary_color, 1.5))
        p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 18, 18)

        # === Decorative top accent line ===
        accent_start = QColor(palette['primary'])
        accent_start.setAlpha(0)
        accent_mid = QColor(palette['primary'])
        accent_mid.setAlpha(200)
        accent_end = QColor(palette['primary_hover'])
        accent_end.setAlpha(0)

        accent_grad = QLinearGradient(rect.width() * 0.2, 0, rect.width() * 0.8, 0)
        accent_grad.setColorAt(0.0, accent_start)
        accent_grad.setColorAt(0.3, accent_mid)
        accent_grad.setColorAt(0.7, accent_mid)
        accent_grad.setColorAt(1.0, accent_end)
        p.setPen(QPen(accent_grad, 2))
        p.drawLine(int(rect.width() * 0.15), 2, int(rect.width() * 0.85), 2)

        # === Logo "INTEGRA" ===
        p.setPen(QColor(palette['primary']))
        logo_font = get_font(FONT_SIZE_LOGO, FONT_WEIGHT_BOLD)
        logo_font.setLetterSpacing(logo_font.AbsoluteSpacing, 14)
        p.setFont(logo_font)
        p.drawText(rect.adjusted(0, -50, 0, 0), int(Qt.AlignHCenter | Qt.AlignVCenter), "INTEGRA")

        # === Subtitle ===
        p.setPen(QColor(palette['text_secondary']))
        p.setFont(get_font(FONT_SIZE_SUBTITLE))
        p.drawText(rect.adjusted(0, 30, 0, 0), int(Qt.AlignHCenter | Qt.AlignVCenter), "Integrated Management System")

        # === Arabic subtitle ===
        p.setPen(QColor(palette['text_muted']))
        p.setFont(get_font(FONT_SIZE_BODY))
        p.drawText(rect.adjusted(0, 65, 0, 0), int(Qt.AlignHCenter | Qt.AlignVCenter), "\u0646\u0638\u0627\u0645 \u0627\u0644\u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u062a\u0643\u0627\u0645\u0644")

        # === Version badge ===
        p.setPen(QColor(palette['text_muted']))
        p.setFont(get_font(FONT_SIZE_TINY))
        p.drawText(rect.adjusted(0, 100, 0, 0), int(Qt.AlignHCenter | Qt.AlignVCenter), f"v{APP_VERSION}")

        # === Progress bar ===
        bar_y = rect.height() - 55
        bar_x = 50
        bar_w = rect.width() - 100
        bar_h = 3

        # Bar background
        bar_bg = QRectF(bar_x, bar_y, bar_w, bar_h)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(palette['bg_card']))
        p.drawRoundedRect(bar_bg, 1.5, 1.5)

        # Bar fill
        if self._progress > 0:
            fill_w = bar_w * (min(self._progress, 100) / 100)
            fill_rect = QRectF(bar_x, bar_y, fill_w, bar_h)
            fill_grad = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
            fill_grad.setColorAt(0.0, QColor(palette['primary']))
            fill_grad.setColorAt(1.0, QColor(palette['info']))
            p.setBrush(fill_grad)
            p.drawRoundedRect(fill_rect, 1.5, 1.5)

        # === Status text with animated dots ===
        dots = "." * self._dots_count
        status_text = f"{self._status}{dots}" if self._status else ""
        p.setPen(QColor(palette['text_muted']))
        p.setFont(get_font(FONT_SIZE_SMALL))
        status_rect = QRectF(bar_x, bar_y + 10, bar_w, 25)
        p.drawText(status_rect, int(Qt.AlignHCenter | Qt.AlignTop), status_text)

        p.end()

    def set_progress(self, value: int, status: str = ""):
        """Update progress and status text."""
        self._progress = value
        if status:
            self._status = status
        self.update()
        QApplication.processEvents()

    def finish(self):
        """Close splash screen."""
        self._dot_timer.stop()
        self.close()
