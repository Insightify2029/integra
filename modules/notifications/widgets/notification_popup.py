"""
INTEGRA - Notification Popup
المحور J2: قائمة الإشعارات المنبثقة

تظهر عند النقر على الجرس وتعرض:
- أحدث 5 إشعارات
- زر "تحديد الكل كمقروء"
- زر "عرض كل الإشعارات"
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QCursor

from core.logging import app_logger
from core.themes import get_current_palette, get_font, FONT_SIZE_BODY, FONT_SIZE_SMALL, FONT_WEIGHT_BOLD


class NotificationPopup(QFrame):
    """
    قائمة الإشعارات المنبثقة

    Signals:
        notification_clicked: عند النقر على إشعار
        view_all_clicked: عند النقر على "عرض الكل"
    """

    notification_clicked = pyqtSignal(int)
    view_all_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

    def _setup_ui(self):
        """إعداد الواجهة"""
        p = get_current_palette()
        self.setFixedWidth(350)
        self.setMaximumHeight(450)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {p['bg_card']};
                border: 1px solid {p['border']};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Notifications list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {p['bg_card']};
            }}
        """)

        self.notifications_container = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_container)
        self.notifications_layout.setContentsMargins(8, 8, 8, 8)
        self.notifications_layout.setSpacing(8)
        self.notifications_layout.addStretch()

        self.scroll_area.setWidget(self.notifications_container)
        layout.addWidget(self.scroll_area)

        # Footer
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """إنشاء رأس القائمة"""
        p = get_current_palette()
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {p['bg_main']};
                border-bottom: 1px solid {p['border']};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 10, 12, 10)

        # العنوان
        title = QLabel("الإشعارات")
        title.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))
        title.setStyleSheet(f"color: {p['text_primary']}; border: none;")
        layout.addWidget(title)

        layout.addStretch()

        # زر تحديد الكل كمقروء
        mark_all_btn = QPushButton("تحديد الكل كمقروء")
        mark_all_btn.setCursor(QCursor(Qt.PointingHandCursor))
        mark_all_btn.setFont(get_font(FONT_SIZE_SMALL))
        mark_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {p['primary']};
                border: none;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                color: {p['primary_hover']};
                text-decoration: underline;
            }}
        """)
        mark_all_btn.clicked.connect(self._mark_all_read)
        layout.addWidget(mark_all_btn)

        return header

    def _create_footer(self) -> QWidget:
        """إنشاء ذيل القائمة"""
        p = get_current_palette()
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {p['bg_main']};
                border-top: 1px solid {p['border']};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(12, 8, 12, 8)

        # زر عرض الكل
        view_all_btn = QPushButton("عرض كل الإشعارات")
        view_all_btn.setCursor(QCursor(Qt.PointingHandCursor))
        view_all_btn.setFont(get_font(FONT_SIZE_BODY))
        view_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p['primary']};
                color: {p['text_on_primary']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {p['primary_hover']};
            }}
        """)
        view_all_btn.clicked.connect(self._on_view_all)
        layout.addWidget(view_all_btn, 1)

        return footer

    def refresh(self):
        """تحديث قائمة الإشعارات"""
        # مسح الإشعارات الحالية
        self._clear_notifications()

        try:
            from ..models import get_notifications

            notifications = get_notifications(is_read=None, limit=5)

            if not notifications:
                self._show_empty_state()
            else:
                for notification in notifications:
                    card = self._create_notification_card(notification)
                    self.notifications_layout.insertWidget(
                        self.notifications_layout.count() - 1,
                        card
                    )

        except Exception as e:
            app_logger.error(f"Error refreshing notifications: {e}")
            self._show_error_state()

    def _clear_notifications(self):
        """مسح الإشعارات الحالية"""
        while self.notifications_layout.count() > 1:  # Keep the stretch
            item = self.notifications_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _create_notification_card(self, notification) -> QWidget:
        """إنشاء بطاقة إشعار"""
        from .notification_card import NotificationCard
        card = NotificationCard(notification, compact=True)
        card.clicked.connect(lambda: self._on_notification_clicked(notification.id))
        return card

    def _show_empty_state(self):
        """عرض حالة الفراغ"""
        p = get_current_palette()
        empty_label = QLabel("لا توجد إشعارات")
        empty_label.setFont(get_font(FONT_SIZE_BODY))
        empty_label.setStyleSheet(f"color: {p['text_muted']}; padding: 20px;")
        empty_label.setAlignment(Qt.AlignCenter)
        self.notifications_layout.insertWidget(0, empty_label)

    def _show_error_state(self):
        """عرض حالة الخطأ"""
        p = get_current_palette()
        error_label = QLabel("حدث خطأ في تحميل الإشعارات")
        error_label.setFont(get_font(FONT_SIZE_BODY))
        error_label.setStyleSheet(f"color: {p['danger']}; padding: 20px;")
        error_label.setAlignment(Qt.AlignCenter)
        self.notifications_layout.insertWidget(0, error_label)

    def _on_notification_clicked(self, notification_id: int):
        """معالجة النقر على إشعار"""
        try:
            from ..models import mark_as_read
            mark_as_read(notification_id)
        except Exception as e:
            app_logger.error(f"Error marking notification as read: {e}")

        self.notification_clicked.emit(notification_id)

    def _on_view_all(self):
        """معالجة النقر على "عرض الكل"""
        self.hide()
        self.view_all_clicked.emit()

    def _mark_all_read(self):
        """تحديد كل الإشعارات كمقروءة"""
        try:
            from ..models import mark_all_as_read
            mark_all_as_read()
            self.refresh()
        except Exception as e:
            app_logger.error(f"Error marking all as read: {e}")
