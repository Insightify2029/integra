"""
INTEGRA - Notification Bell Widget
المحور J2: أيقونة الجرس

أيقونة تظهر في أعلى الشاشة مع:
- Badge يعرض عدد الإشعارات غير المقروءة
- قائمة منبثقة بالإشعارات الأخيرة عند النقر
- تحديث تلقائي للعدد
"""

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QMenu, QAction, QWidgetAction,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint, QSize
from PyQt5.QtGui import QFont, QCursor

from core.logging import app_logger


class NotificationBadge(QLabel):
    """Badge يعرض عدد الإشعارات"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._count = 0
        self._setup_ui()

    def _setup_ui(self):
        """إعداد الواجهة"""
        self.setFixedSize(20, 20)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Cairo", 9, QFont.Bold))
        self._update_style()
        self.hide()

    def _update_style(self):
        """تحديث التنسيق"""
        self.setStyleSheet("""
            QLabel {
                background-color: #e74c3c;
                color: white;
                border-radius: 10px;
                padding: 2px;
                min-width: 16px;
                min-height: 16px;
            }
        """)

    def set_count(self, count: int):
        """تحديث العدد"""
        self._count = count
        if count > 0:
            if count > 99:
                self.setText("99+")
            else:
                self.setText(str(count))
            self.show()
        else:
            self.hide()

    @property
    def count(self) -> int:
        return self._count


class NotificationBell(QWidget):
    """
    أيقونة الجرس مع Badge

    Signals:
        clicked: عند النقر على الجرس
        notification_clicked: عند النقر على إشعار معين
        view_all_clicked: عند النقر على "عرض الكل"
    """

    clicked = pyqtSignal()
    notification_clicked = pyqtSignal(int)  # notification_id
    view_all_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup = None
        self._refresh_timer = None
        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self):
        """إعداد الواجهة"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # زر الجرس
        self.bell_button = QPushButton()
        self.bell_button.setFixedSize(40, 40)
        self.bell_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.bell_button.setToolTip("الإشعارات")
        self.bell_button.clicked.connect(self._on_bell_clicked)

        # تعيين الأيقونة
        try:
            from core.utils import icon
            self.bell_button.setIcon(icon("fa5s.bell", color="#555"))
            self.bell_button.setIconSize(QSize(20, 20))
        except ImportError:
            self.bell_button.setText("🔔")

        self.bell_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)

        layout.addWidget(self.bell_button)

        # Badge
        self.badge = NotificationBadge(self)
        self.badge.move(22, 2)

        self.setFixedSize(44, 44)

    def _setup_timer(self):
        """إعداد مؤقت التحديث التلقائي"""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh_count)
        self._refresh_timer.start(30000)  # كل 30 ثانية

    def _on_bell_clicked(self):
        """معالجة النقر على الجرس"""
        self.clicked.emit()
        self._show_popup()

    def _show_popup(self):
        """عرض القائمة المنبثقة"""
        from .notification_popup import NotificationPopup

        if self._popup is None:
            self._popup = NotificationPopup(self)
            self._popup.notification_clicked.connect(self.notification_clicked.emit)
            self._popup.view_all_clicked.connect(self.view_all_clicked.emit)
            self._popup.notification_clicked.connect(lambda: self._popup.hide())

        # حساب موقع العرض
        button_pos = self.bell_button.mapToGlobal(QPoint(0, self.bell_button.height()))
        popup_x = button_pos.x() - self._popup.width() + self.bell_button.width()
        popup_y = button_pos.y() + 5

        self._popup.move(popup_x, popup_y)
        self._popup.refresh()
        self._popup.show()

    def refresh_count(self):
        """تحديث عدد الإشعارات"""
        try:
            from ..models import get_unread_count
            count = get_unread_count()
            self.badge.set_count(count)
        except Exception as e:
            app_logger.debug(f"Error refreshing notification count: {e}")

    def set_count(self, count: int):
        """تعيين العدد يدوياً"""
        self.badge.set_count(count)

    @property
    def unread_count(self) -> int:
        """عدد الإشعارات غير المقروءة"""
        return self.badge.count

    def start_refresh(self, interval_ms: int = 30000):
        """بدء التحديث التلقائي"""
        self._refresh_timer.start(interval_ms)

    def stop_refresh(self):
        """إيقاف التحديث التلقائي"""
        self._refresh_timer.stop()


def create_notification_bell(parent=None) -> NotificationBell:
    """
    إنشاء أيقونة الجرس

    Args:
        parent: العنصر الأب

    Returns:
        NotificationBell widget

    Example:
        >>> bell = create_notification_bell(self)
        >>> bell.notification_clicked.connect(self.on_notification_clicked)
        >>> bell.view_all_clicked.connect(self.open_notification_center)
        >>> toolbar.addWidget(bell)
    """
    bell = NotificationBell(parent)
    bell.refresh_count()
    return bell
