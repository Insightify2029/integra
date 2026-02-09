"""
INTEGRA - Notification Card Widget
المحور J2/J3: بطاقة الإشعار

تعرض إشعار واحد مع:
- أيقونة النوع
- العنوان والمحتوى
- الوقت
- أزرار الإجراءات
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QCursor, QColor

from core.logging import app_logger
from core.themes import get_current_palette, get_font, FONT_SIZE_BODY, FONT_SIZE_SMALL, FONT_SIZE_TINY, FONT_WEIGHT_BOLD


class NotificationCard(QFrame):
    """
    بطاقة إشعار

    Signals:
        clicked: عند النقر على البطاقة
        action_clicked: عند النقر على إجراء (action_id)
    """

    clicked = pyqtSignal()
    action_clicked = pyqtSignal(str)  # action_id

    def __init__(self, notification, compact: bool = False, parent=None):
        super().__init__(parent)
        self.notification = notification
        self.compact = compact
        self._setup_ui()

    def _setup_ui(self):
        """إعداد الواجهة"""
        p = get_current_palette()
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # التنسيق حسب حالة القراءة
        bg_color = p['bg_main'] if self.notification.is_read else p['bg_card']
        border_color = self.notification.priority_color

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {p['border']};
                border-left: 3px solid {border_color};
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: {p['bg_hover']};
                border-color: {p['primary']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # الصف العلوي: أيقونة + عنوان + وقت
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # أيقونة النوع
        type_icon = self._create_type_icon()
        top_row.addWidget(type_icon)

        # العنوان
        title_label = QLabel(self.notification.title)
        title_label.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD if not self.notification.is_read else None))
        title_label.setStyleSheet(f"color: {p['text_primary'] if not self.notification.is_read else p['text_muted']}; border: none;")
        title_label.setWordWrap(True)
        top_row.addWidget(title_label, 1)

        # الوقت
        time_label = QLabel(self.notification.time_ago)
        time_label.setFont(get_font(FONT_SIZE_TINY))
        time_label.setStyleSheet(f"color: {p['text_muted']}; border: none;")
        top_row.addWidget(time_label)

        layout.addLayout(top_row)

        # المحتوى (إذا موجود وليس compact)
        if self.notification.body and not self.compact:
            body_label = QLabel(self._truncate_text(self.notification.body, 150))
            body_label.setFont(get_font(FONT_SIZE_SMALL))
            body_label.setStyleSheet(f"color: {p['text_secondary']}; border: none;")
            body_label.setWordWrap(True)
            layout.addWidget(body_label)

        # أزرار الإجراءات (إذا موجودة وليس compact)
        if self.notification.actions and not self.compact:
            actions_row = self._create_actions_row()
            layout.addLayout(actions_row)

        # Badge للأولوية العاجلة
        if self.notification.is_urgent:
            urgent_badge = self._create_urgent_badge()
            layout.addWidget(urgent_badge)

    def _create_type_icon(self) -> QLabel:
        """إنشاء أيقونة النوع"""
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)

        try:
            from core.utils import icon
            icon_name = self.notification.type_icon
            color = self.notification.type_color
            qicon = icon(icon_name, color=color)
            icon_label.setPixmap(qicon.pixmap(QSize(20, 20)))
        except ImportError:
            # Fallback to emoji
            type_emojis = {
                "email": "📧",
                "task": "✅",
                "calendar": "📅",
                "system": "⚙️",
                "ai": "🤖",
                "alert": "⚠️",
            }
            emoji = type_emojis.get(self.notification.notification_type.value, "🔔")
            icon_label.setText(emoji)
            icon_label.setStyleSheet("font-size: 14px; border: none;")

        icon_label.setStyleSheet("border: none;")
        return icon_label

    def _create_actions_row(self) -> QHBoxLayout:
        """إنشاء صف الإجراءات"""
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addStretch()

        for action in self.notification.actions[:3]:  # حد أقصى 3 إجراءات
            btn = QPushButton(action.label)
            btn.setFont(get_font(FONT_SIZE_SMALL))
            btn.setCursor(QCursor(Qt.PointingHandCursor))

            if action.is_primary:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {p['primary']};
                        color: {p['text_on_primary']};
                        border: none;
                        border-radius: 4px;
                        padding: 4px 12px;
                    }}
                    QPushButton:hover {{
                        background-color: {p['primary_hover']};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {p['primary']};
                        border: 1px solid {p['primary']};
                        border-radius: 4px;
                        padding: 4px 12px;
                    }}
                    QPushButton:hover {{
                        background-color: {p['bg_hover']};
                    }}
                """)

            btn.clicked.connect(lambda checked, a=action: self._on_action_clicked(a.id))
            row.addWidget(btn)

        return row

    def _create_urgent_badge(self) -> QLabel:
        """إنشاء شارة العاجل"""
        p = get_current_palette()
        badge = QLabel("عاجل")
        badge.setFont(get_font(FONT_SIZE_TINY, FONT_WEIGHT_BOLD))
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {p['danger']};
                color: {p['text_on_primary']};
                border-radius: 3px;
                padding: 2px 6px;
            }}
        """)
        badge.setFixedWidth(40)
        badge.setAlignment(Qt.AlignCenter)
        return badge

    def _truncate_text(self, text: str, max_length: int) -> str:
        """قص النص الطويل"""
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(' ', 1)[0] + "..."

    def _on_action_clicked(self, action_id: str):
        """معالجة النقر على إجراء"""
        self.action_clicked.emit(action_id)

    def mousePressEvent(self, event):
        """معالجة النقر على البطاقة"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
