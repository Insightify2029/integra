"""
INTEGRA - Notification Center Screen
المحور J3: صفحة مركز الإشعارات

صفحة كاملة لعرض وإدارة الإشعارات:
- قائمة كاملة بكل الإشعارات
- فلترة حسب: النوع، الأولوية، الحالة
- بحث في الإشعارات
- إجراءات جماعية
- تجميع حسب اليوم
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QLineEdit,
    QComboBox, QCheckBox, QSizePolicy, QStackedWidget,
    QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QCursor

from core.logging import app_logger


class NotificationCenterScreen(QWidget):
    """
    صفحة مركز الإشعارات

    Signals:
        notification_clicked: عند النقر على إشعار
        action_clicked: عند النقر على إجراء
    """

    notification_clicked = pyqtSignal(int)
    action_clicked = pyqtSignal(int, str)  # notification_id, action_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_filter_type = None
        self._current_filter_priority = None
        self._current_filter_read = None
        self._search_text = ""
        self._setup_ui()

    def _setup_ui(self):
        """إعداد الواجهة"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Filters
        filters = self._create_filters()
        layout.addWidget(filters)

        # Stats bar
        self.stats_bar = self._create_stats_bar()
        layout.addWidget(self.stats_bar)

        # Content area (stacked widget for list/empty state)
        self.content_stack = QStackedWidget()

        # Notifications list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self.notifications_container = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_container)
        self.notifications_layout.setContentsMargins(0, 0, 0, 0)
        self.notifications_layout.setSpacing(12)
        self.notifications_layout.addStretch()

        self.scroll_area.setWidget(self.notifications_container)
        self.content_stack.addWidget(self.scroll_area)

        # Empty state
        self.empty_state = self._create_empty_state()
        self.content_stack.addWidget(self.empty_state)

        layout.addWidget(self.content_stack, 1)

        # Initial load
        QTimer.singleShot(100, self.refresh)

    def _create_header(self) -> QWidget:
        """إنشاء رأس الصفحة"""
        header = QFrame()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        # العنوان
        title = QLabel("🔔 مركز الإشعارات")
        title.setFont(QFont("Cairo", 18, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        layout.addStretch()

        # أزرار الإجراءات
        mark_all_btn = QPushButton("تحديد الكل كمقروء")
        mark_all_btn.setFont(QFont("Cairo", 10))
        mark_all_btn.setCursor(QCursor(Qt.PointingHandCursor))
        mark_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        mark_all_btn.clicked.connect(self._mark_all_read)
        layout.addWidget(mark_all_btn)

        settings_btn = QPushButton("⚙️ الإعدادات")
        settings_btn.setFont(QFont("Cairo", 10))
        settings_btn.setCursor(QCursor(Qt.PointingHandCursor))
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #333;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #bdc3c7;
            }
        """)
        settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(settings_btn)

        return header

    def _create_filters(self) -> QWidget:
        """إنشاء شريط الفلاتر"""
        filters = QFrame()
        filters.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout = QHBoxLayout(filters)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # البحث
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 بحث في الإشعارات...")
        self.search_input.setFont(QFont("Cairo", 10))
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)

        layout.addStretch()

        # فلتر النوع
        type_label = QLabel("النوع:")
        type_label.setFont(QFont("Cairo", 10))
        layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.setFont(QFont("Cairo", 10))
        self.type_combo.addItem("الكل", None)
        self.type_combo.addItem("📧 إيميل", "email")
        self.type_combo.addItem("✅ مهام", "task")
        self.type_combo.addItem("📅 تقويم", "calendar")
        self.type_combo.addItem("⚙️ نظام", "system")
        self.type_combo.addItem("🤖 AI", "ai")
        self.type_combo.addItem("⚠️ تنبيه", "alert")
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 100px;
            }
        """)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        layout.addWidget(self.type_combo)

        # فلتر الأولوية
        priority_label = QLabel("الأولوية:")
        priority_label.setFont(QFont("Cairo", 10))
        layout.addWidget(priority_label)

        self.priority_combo = QComboBox()
        self.priority_combo.setFont(QFont("Cairo", 10))
        self.priority_combo.addItem("الكل", None)
        self.priority_combo.addItem("🔴 عاجل", "urgent")
        self.priority_combo.addItem("🟠 مهم", "high")
        self.priority_combo.addItem("🔵 عادي", "normal")
        self.priority_combo.addItem("⚪ منخفض", "low")
        self.priority_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 100px;
            }
        """)
        self.priority_combo.currentIndexChanged.connect(self._on_priority_changed)
        layout.addWidget(self.priority_combo)

        # فلتر حالة القراءة
        self.unread_only = QCheckBox("غير المقروءة فقط")
        self.unread_only.setFont(QFont("Cairo", 10))
        self.unread_only.stateChanged.connect(self._on_unread_changed)
        layout.addWidget(self.unread_only)

        return filters

    def _create_stats_bar(self) -> QWidget:
        """إنشاء شريط الإحصائيات"""
        stats = QFrame()
        layout = QHBoxLayout(stats)
        layout.setContentsMargins(0, 0, 0, 0)

        self.total_label = QLabel("إجمالي: 0")
        self.total_label.setFont(QFont("Cairo", 10))
        self.total_label.setStyleSheet("color: #666;")
        layout.addWidget(self.total_label)

        self.unread_label = QLabel("غير مقروء: 0")
        self.unread_label.setFont(QFont("Cairo", 10))
        self.unread_label.setStyleSheet("color: #e74c3c;")
        layout.addWidget(self.unread_label)

        layout.addStretch()

        return stats

    def _create_empty_state(self) -> QWidget:
        """إنشاء حالة الفراغ"""
        empty = QWidget()
        layout = QVBoxLayout(empty)
        layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel("🔔")
        icon_label.setFont(QFont("Segoe UI Emoji", 48))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel("لا توجد إشعارات")
        text_label.setFont(QFont("Cairo", 14))
        text_label.setStyleSheet("color: #888;")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)

        hint_label = QLabel("ستظهر الإشعارات الجديدة هنا")
        hint_label.setFont(QFont("Cairo", 10))
        hint_label.setStyleSheet("color: #aaa;")
        hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint_label)

        return empty

    def refresh(self):
        """تحديث قائمة الإشعارات"""
        self._clear_notifications()

        try:
            from ..models import (
                get_notifications, get_unread_count,
                NotificationType, NotificationPriority
            )

            # تحديد الفلاتر
            notification_type = None
            if self._current_filter_type:
                notification_type = NotificationType(self._current_filter_type)

            priority = None
            if self._current_filter_priority:
                priority = NotificationPriority(self._current_filter_priority)

            is_read = None
            if self._current_filter_read is not None:
                is_read = not self._current_filter_read  # Checkbox is "unread only"

            # جلب الإشعارات
            notifications = get_notifications(
                notification_type=notification_type,
                priority=priority,
                is_read=is_read,
                limit=100,
            )

            # فلترة بالبحث
            if self._search_text:
                search_lower = self._search_text.lower()
                notifications = [
                    n for n in notifications
                    if search_lower in n.title.lower() or
                       (n.body and search_lower in n.body.lower())
                ]

            # تحديث الإحصائيات
            unread_count = get_unread_count()
            self.total_label.setText(f"إجمالي: {len(notifications)}")
            self.unread_label.setText(f"غير مقروء: {unread_count}")

            if not notifications:
                self.content_stack.setCurrentWidget(self.empty_state)
            else:
                self.content_stack.setCurrentWidget(self.scroll_area)
                self._group_and_display_notifications(notifications)

        except Exception as e:
            app_logger.error(f"Error refreshing notification center: {e}")
            self.content_stack.setCurrentWidget(self.empty_state)

    def _clear_notifications(self):
        """مسح الإشعارات الحالية"""
        while self.notifications_layout.count() > 1:
            item = self.notifications_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _group_and_display_notifications(self, notifications: list):
        """تجميع وعرض الإشعارات حسب اليوم"""
        from datetime import date, datetime

        groups = {}
        today = date.today()

        for notification in notifications:
            if notification.created_at:
                notification_date = notification.created_at.date()
                if notification_date == today:
                    group_key = "اليوم"
                elif notification_date == today.replace(day=today.day - 1):
                    group_key = "أمس"
                else:
                    group_key = notification_date.strftime("%Y/%m/%d")
            else:
                group_key = "غير محدد"

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(notification)

        # عرض المجموعات
        for group_name, group_notifications in groups.items():
            # عنوان المجموعة
            group_header = QLabel(group_name)
            group_header.setFont(QFont("Cairo", 11, QFont.Bold))
            group_header.setStyleSheet("color: #666; padding: 8px 0;")
            self.notifications_layout.insertWidget(
                self.notifications_layout.count() - 1,
                group_header
            )

            # بطاقات الإشعارات
            for notification in group_notifications:
                card = self._create_notification_card(notification)
                self.notifications_layout.insertWidget(
                    self.notifications_layout.count() - 1,
                    card
                )

    def _create_notification_card(self, notification) -> QWidget:
        """إنشاء بطاقة إشعار"""
        from ..widgets import NotificationCard
        card = NotificationCard(notification, compact=False)
        card.clicked.connect(lambda: self._on_notification_clicked(notification))
        card.action_clicked.connect(
            lambda action_id: self._on_action_clicked(notification.id, action_id)
        )
        return card

    def _on_notification_clicked(self, notification):
        """معالجة النقر على إشعار"""
        try:
            from ..models import mark_as_read
            if not notification.is_read:
                mark_as_read(notification.id)
                self.refresh()
        except Exception as e:
            app_logger.error(f"Error handling notification click: {e}")

        self.notification_clicked.emit(notification.id)

    def _on_action_clicked(self, notification_id: int, action_id: str):
        """معالجة النقر على إجراء"""
        self.action_clicked.emit(notification_id, action_id)

    def _on_search_changed(self, text: str):
        """معالجة تغيير نص البحث"""
        self._search_text = text
        self.refresh()

    def _on_type_changed(self, index: int):
        """معالجة تغيير فلتر النوع"""
        self._current_filter_type = self.type_combo.currentData()
        self.refresh()

    def _on_priority_changed(self, index: int):
        """معالجة تغيير فلتر الأولوية"""
        self._current_filter_priority = self.priority_combo.currentData()
        self.refresh()

    def _on_unread_changed(self, state: int):
        """معالجة تغيير فلتر القراءة"""
        self._current_filter_read = state == Qt.Checked
        self.refresh()

    def _mark_all_read(self):
        """تحديد كل الإشعارات كمقروءة"""
        try:
            from ..models import mark_all_as_read
            mark_all_as_read()
            self.refresh()
        except Exception as e:
            app_logger.error(f"Error marking all as read: {e}")

    def _open_settings(self):
        """فتح إعدادات الإشعارات"""
        QMessageBox.information(
            self,
            "قريباً",
            "إعدادات الإشعارات ستكون متاحة قريباً"
        )
