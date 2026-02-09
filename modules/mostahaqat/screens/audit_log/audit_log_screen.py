"""
Audit Log Screen
================
شاشة سجل التدقيق - عرض جميع التغييرات على قاعدة البيانات

Features:
- View all INSERT / UPDATE / DELETE operations
- Filter by table, action type, date range
- Pagination for large result sets
- Detail dialog showing old vs new values
- Statistics summary cards
- Background data loading (Rule 13)
- Theme-aware (dark/light)
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QComboBox, QDateEdit, QHeaderView, QDialog,
    QTextEdit, QSplitter, QGridLayout,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

from core.themes import get_font, FONT_SIZE_TITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL, FONT_SIZE_TINY, FONT_WEIGHT_BOLD

from core.database.audit.audit_manager import get_audit_manager
from core.threading import run_in_background
from core.logging import app_logger

# Arabic labels for action types
ACTION_LABELS = {
    "INSERT": "إضافة",
    "UPDATE": "تعديل",
    "DELETE": "حذف",
}

# Arabic labels for table names
TABLE_LABELS = {
    "employees": "الموظفين",
    "companies": "الشركات",
    "departments": "الأقسام",
    "job_titles": "المسميات الوظيفية",
    "banks": "البنوك",
    "employee_statuses": "حالات الموظفين",
    "nationalities": "الجنسيات",
}

RECORDS_PER_PAGE = 50


def _get_action_color(action: str, palette: QPalette) -> QColor:
    """
    Get a theme-aware color for an action type.
    Uses palette highlight as fallback base.
    """
    bg = palette.color(QPalette.Base)
    is_dark = bg.lightness() < 128

    colors = {
        "INSERT": QColor("#22c55e") if is_dark else QColor("#16a34a"),
        "UPDATE": QColor("#60a5fa") if is_dark else QColor("#2563eb"),
        "DELETE": QColor("#f87171") if is_dark else QColor("#dc2626"),
    }
    return colors.get(action, palette.color(QPalette.Text))


class StatCard(QFrame):
    """A statistics card with a value and label."""

    def __init__(
        self, label: str, value: str = "0",
        accent_action: Optional[str] = None, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setFixedHeight(70)

        self._accent_action = accent_action

        vl = QVBoxLayout(self)
        vl.setContentsMargins(12, 8, 12, 8)
        vl.setSpacing(2)

        self._value_label = QLabel(value)
        self._value_label.setFont(get_font(FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
        self._value_label.setAlignment(Qt.AlignCenter)
        self._value_label.setObjectName("statValue")
        if accent_action:
            color = _get_action_color(accent_action, self.palette())
            self._value_label.setStyleSheet(f"color: {color.name()};")
        vl.addWidget(self._value_label)

        name_lbl = QLabel(label)
        name_lbl.setFont(get_font(FONT_SIZE_SMALL))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setObjectName("statLabel")
        vl.addWidget(name_lbl)

    def set_value(self, value: str) -> None:
        """Update the displayed value."""
        self._value_label.setText(value)


class AuditLogScreen(QWidget):
    """
    Audit Log Viewer Screen.
    Shows audit trail records with filters, pagination, and detail view.

    Signals:
        back_clicked(): User wants to go back
    """

    back_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._manager = get_audit_manager()
        self._current_page = 0
        self._total_count = 0
        self._loading = False

        self._setup_ui()
        self._load_data()

    # ----------------------------------------------------------------
    # UI Setup
    # ----------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the full screen layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Header
        layout.addWidget(self._build_header())

        # Statistics cards
        layout.addWidget(self._build_stats_bar())

        # Filters
        layout.addWidget(self._build_filter_bar())

        # Table
        self._table = self._build_table()
        layout.addWidget(self._table, 1)

        # Pagination bar
        layout.addWidget(self._build_pagination_bar())

    def _build_header(self) -> QWidget:
        """Build the header bar with title and back button."""
        header = QFrame()
        header.setObjectName("auditHeader")

        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)

        # Back button
        back_btn = QPushButton("رجوع")
        back_btn.setFont(get_font(FONT_SIZE_SMALL))
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self.back_clicked.emit)
        hl.addWidget(back_btn)

        hl.addStretch()

        # Title
        title = QLabel("سجل التدقيق  |  Audit Trail")
        title.setFont(get_font(FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)

        hl.addStretch()

        # Refresh button
        self._btn_refresh = QPushButton("تحديث")
        self._btn_refresh.setFont(get_font(FONT_SIZE_SMALL))
        self._btn_refresh.setCursor(Qt.PointingHandCursor)
        self._btn_refresh.setFixedWidth(100)
        self._btn_refresh.clicked.connect(self._load_data)
        hl.addWidget(self._btn_refresh)

        return header

    def _build_stats_bar(self) -> QWidget:
        """Build the statistics summary cards."""
        frame = QFrame()
        frame.setObjectName("auditStats")

        hl = QHBoxLayout(frame)
        hl.setContentsMargins(0, 5, 0, 5)
        hl.setSpacing(10)

        self._stat_total = StatCard("الإجمالي")
        self._stat_insert = StatCard("إضافة", accent_action="INSERT")
        self._stat_update = StatCard("تعديل", accent_action="UPDATE")
        self._stat_delete = StatCard("حذف", accent_action="DELETE")
        self._stat_tables = StatCard("جداول مراقَبة")

        hl.addWidget(self._stat_total)
        hl.addWidget(self._stat_insert)
        hl.addWidget(self._stat_update)
        hl.addWidget(self._stat_delete)
        hl.addWidget(self._stat_tables)

        return frame

    def _build_filter_bar(self) -> QWidget:
        """Build the filter controls bar."""
        bar = QFrame()
        bar.setObjectName("auditFilterBar")

        hl = QHBoxLayout(bar)
        hl.setContentsMargins(5, 5, 5, 5)
        hl.setSpacing(10)

        cairo = get_font(FONT_SIZE_SMALL)

        # Table filter
        lbl_table = QLabel("الجدول:")
        lbl_table.setFont(cairo)
        hl.addWidget(lbl_table)

        self._cmb_table = QComboBox()
        self._cmb_table.setFont(cairo)
        self._cmb_table.setMinimumWidth(140)
        self._cmb_table.addItem("الكل", None)
        for key, label in TABLE_LABELS.items():
            self._cmb_table.addItem(label, key)
        hl.addWidget(self._cmb_table)

        # Action type filter
        lbl_action = QLabel("العملية:")
        lbl_action.setFont(cairo)
        hl.addWidget(lbl_action)

        self._cmb_action = QComboBox()
        self._cmb_action.setFont(cairo)
        self._cmb_action.setMinimumWidth(100)
        self._cmb_action.addItem("الكل", None)
        for key, label in ACTION_LABELS.items():
            self._cmb_action.addItem(label, key)
        hl.addWidget(self._cmb_action)

        # Date range
        lbl_from = QLabel("من:")
        lbl_from.setFont(cairo)
        hl.addWidget(lbl_from)

        self._date_from = QDateEdit()
        self._date_from.setFont(cairo)
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        self._date_from.setDate(QDate.currentDate().addDays(-30))
        hl.addWidget(self._date_from)

        lbl_to = QLabel("إلى:")
        lbl_to.setFont(cairo)
        hl.addWidget(lbl_to)

        self._date_to = QDateEdit()
        self._date_to.setFont(cairo)
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        self._date_to.setDate(QDate.currentDate())
        hl.addWidget(self._date_to)

        hl.addStretch()

        # Search button
        self._btn_search = QPushButton("بحث")
        self._btn_search.setFont(get_font(FONT_SIZE_SMALL, FONT_WEIGHT_BOLD))
        self._btn_search.setCursor(Qt.PointingHandCursor)
        self._btn_search.setFixedWidth(90)
        self._btn_search.clicked.connect(self._on_search)
        hl.addWidget(self._btn_search)

        # Reset button
        reset_btn = QPushButton("إعادة تعيين")
        reset_btn.setFont(cairo)
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setFixedWidth(100)
        reset_btn.clicked.connect(self._on_reset_filters)
        hl.addWidget(reset_btn)

        return bar

    def _build_table(self) -> QTableWidget:
        """Build the main data table."""
        table = QTableWidget()
        table.setFont(get_font(FONT_SIZE_SMALL))

        headers = [
            "#",
            "التاريخ والوقت",
            "الجدول",
            "العملية",
            "رقم السجل",
            "الحقول المتغيرة",
            "المستخدم",
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        # Header styling
        header = table.horizontalHeader()
        header.setFont(get_font(FONT_SIZE_SMALL, FONT_WEIGHT_BOLD))
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        # Table behaviour
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setLayoutDirection(Qt.RightToLeft)

        # Double-click to see details
        table.doubleClicked.connect(self._on_row_double_click)

        return table

    def _build_pagination_bar(self) -> QWidget:
        """Build the pagination controls."""
        bar = QFrame()
        bar.setObjectName("auditPagination")

        hl = QHBoxLayout(bar)
        hl.setContentsMargins(0, 5, 0, 0)

        cairo = get_font(FONT_SIZE_SMALL)

        self._lbl_page_info = QLabel("")
        self._lbl_page_info.setFont(cairo)
        hl.addWidget(self._lbl_page_info)

        hl.addStretch()

        self._btn_prev = QPushButton("السابق")
        self._btn_prev.setFont(cairo)
        self._btn_prev.setCursor(Qt.PointingHandCursor)
        self._btn_prev.setFixedWidth(80)
        self._btn_prev.clicked.connect(self._on_prev_page)
        hl.addWidget(self._btn_prev)

        self._btn_next = QPushButton("التالي")
        self._btn_next.setFont(cairo)
        self._btn_next.setCursor(Qt.PointingHandCursor)
        self._btn_next.setFixedWidth(80)
        self._btn_next.clicked.connect(self._on_next_page)
        hl.addWidget(self._btn_next)

        return bar

    # ----------------------------------------------------------------
    # Data Loading  (background thread - Rule 13)
    # ----------------------------------------------------------------

    def _get_filters(self) -> Dict[str, Any]:
        """Collect current filter values."""
        table_name = self._cmb_table.currentData()
        action_type = self._cmb_action.currentData()

        from_qdate = self._date_from.date()
        to_qdate = self._date_to.date()

        from_date = datetime(from_qdate.year(), from_qdate.month(), from_qdate.day())
        to_date = datetime(
            to_qdate.year(), to_qdate.month(), to_qdate.day(), 23, 59, 59
        )

        return {
            "table_name": table_name,
            "action_type": action_type,
            "from_date": from_date,
            "to_date": to_date,
        }

    def _load_data(self) -> None:
        """Kick off background data load with current filters."""
        if self._loading:
            return
        self._loading = True
        self._set_loading_state(True)

        filters = self._get_filters()
        page = self._current_page

        def _fetch():
            """Run DB queries in background thread."""
            mgr = get_audit_manager()
            total = mgr.get_total_count(
                table_name=filters["table_name"],
                action_type=filters["action_type"],
                from_date=filters["from_date"],
                to_date=filters["to_date"],
            )
            offset = page * RECORDS_PER_PAGE
            records = mgr.get_audit_history(
                table_name=filters["table_name"],
                action_type=filters["action_type"],
                from_date=filters["from_date"],
                to_date=filters["to_date"],
                limit=RECORDS_PER_PAGE,
                offset=offset,
            )
            stats = mgr.get_audit_statistics(days=30)
            return {"total": total, "records": records, "stats": stats}

        run_in_background(
            _fetch,
            on_finished=self._on_data_loaded,
            on_error=self._on_data_error,
        )

    def _on_data_loaded(self, result: Dict[str, Any]) -> None:
        """Handle successful background data load (called on main thread)."""
        self._loading = False
        self._set_loading_state(False)

        self._total_count = result["total"]
        self._populate_table(result["records"])
        self._update_pagination()
        self._apply_stats(result["stats"])

    def _on_data_error(self, exc_type, message, traceback_str) -> None:
        """Handle background data load failure (called on main thread)."""
        self._loading = False
        self._set_loading_state(False)
        app_logger.error(f"Failed to load audit data: {message}")
        self._lbl_page_info.setText(
            "خطأ في تحميل البيانات - تأكد من اتصال قاعدة البيانات"
        )

    def _set_loading_state(self, loading: bool) -> None:
        """Enable/disable interactive controls during load."""
        self._btn_search.setEnabled(not loading)
        self._btn_refresh.setEnabled(not loading)
        self._btn_prev.setEnabled(not loading)
        self._btn_next.setEnabled(not loading)
        if loading:
            self._lbl_page_info.setText("جارٍ التحميل...")

    def _populate_table(self, records: List[Dict[str, Any]]) -> None:
        """Fill the table widget with audit records."""
        self._table.setRowCount(0)
        self._table.setRowCount(len(records))

        palette = self.palette()

        for row_idx, record in enumerate(records):
            # Store full record as user data on first column
            id_item = QTableWidgetItem(str(record.get("id", "")))
            id_item.setTextAlignment(Qt.AlignCenter)
            id_item.setData(Qt.UserRole, record)
            self._table.setItem(row_idx, 0, id_item)

            # Timestamp
            ts = record.get("action_timestamp")
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else ""
            ts_item = QTableWidgetItem(ts_str)
            ts_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row_idx, 1, ts_item)

            # Table name (Arabic label)
            tbl = record.get("table_name", "")
            tbl_label = TABLE_LABELS.get(tbl, tbl)
            tbl_item = QTableWidgetItem(tbl_label)
            tbl_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row_idx, 2, tbl_item)

            # Action type (theme-aware color)
            action = record.get("action_type", "")
            action_label = ACTION_LABELS.get(action, action)
            action_item = QTableWidgetItem(action_label)
            action_item.setTextAlignment(Qt.AlignCenter)
            action_item.setForeground(_get_action_color(action, palette))
            action_item.setFont(get_font(FONT_SIZE_SMALL, FONT_WEIGHT_BOLD))
            self._table.setItem(row_idx, 3, action_item)

            # Record ID
            rec_id = record.get("record_id", "")
            rec_item = QTableWidgetItem(str(rec_id) if rec_id else "")
            rec_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row_idx, 4, rec_item)

            # Changed fields
            changed = record.get("changed_fields") or []
            changed_str = ", ".join(changed) if changed else "-"
            changed_item = QTableWidgetItem(changed_str)
            changed_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._table.setItem(row_idx, 5, changed_item)

            # App user
            user = record.get("app_user") or record.get("db_user", "")
            user_item = QTableWidgetItem(str(user))
            user_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row_idx, 6, user_item)

    def _update_pagination(self) -> None:
        """Update pagination controls and info label."""
        total_pages = max(
            1, (self._total_count + RECORDS_PER_PAGE - 1) // RECORDS_PER_PAGE
        )
        current_display = self._current_page + 1

        self._lbl_page_info.setText(
            f"صفحة {current_display} من {total_pages}  |  "
            f"إجمالي السجلات: {self._total_count}"
        )

        self._btn_prev.setEnabled(self._current_page > 0)
        self._btn_next.setEnabled(current_display < total_pages)

    def _apply_stats(self, stats: Dict[str, Any]) -> None:
        """Update the statistics cards with pre-fetched data."""
        self._stat_total.set_value(str(stats.get("total", 0)))
        self._stat_insert.set_value(
            str(stats.get("by_action", {}).get("INSERT", 0))
        )
        self._stat_update.set_value(
            str(stats.get("by_action", {}).get("UPDATE", 0))
        )
        self._stat_delete.set_value(
            str(stats.get("by_action", {}).get("DELETE", 0))
        )
        self._stat_tables.set_value(
            str(len(stats.get("audited_tables", [])))
        )

    # ----------------------------------------------------------------
    # Event Handlers
    # ----------------------------------------------------------------

    def _on_search(self) -> None:
        """Handle search button click."""
        self._current_page = 0
        self._load_data()

    def _on_reset_filters(self) -> None:
        """Reset all filters to defaults."""
        self._cmb_table.setCurrentIndex(0)
        self._cmb_action.setCurrentIndex(0)
        self._date_from.setDate(QDate.currentDate().addDays(-30))
        self._date_to.setDate(QDate.currentDate())
        self._current_page = 0
        self._load_data()

    def _on_prev_page(self) -> None:
        """Go to previous page."""
        if self._current_page > 0:
            self._current_page -= 1
            self._load_data()

    def _on_next_page(self) -> None:
        """Go to next page."""
        total_pages = max(
            1, (self._total_count + RECORDS_PER_PAGE - 1) // RECORDS_PER_PAGE
        )
        if self._current_page + 1 < total_pages:
            self._current_page += 1
            self._load_data()

    def _on_row_double_click(self, index) -> None:
        """Show detail dialog for the double-clicked row."""
        row = index.row()
        id_item = self._table.item(row, 0)
        if id_item is None:
            return

        record = id_item.data(Qt.UserRole)
        if record:
            dlg = AuditDetailDialog(record, parent=self)
            dlg.exec_()

    def refresh(self) -> None:
        """Refresh the audit log data."""
        self._load_data()


# ====================================================================
# Detail Dialog
# ====================================================================

class AuditDetailDialog(QDialog):
    """
    Dialog showing full details of a single audit record,
    with side-by-side old vs new values.
    """

    def __init__(
        self, record: Dict[str, Any], parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._record = record
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the detail dialog layout."""
        self.setWindowTitle("تفاصيل التدقيق  |  Audit Detail")
        self.setMinimumSize(750, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        cairo = get_font(FONT_SIZE_SMALL)
        cairo_bold = get_font(FONT_SIZE_SMALL, FONT_WEIGHT_BOLD)

        # Meta info
        meta_frame = QFrame()
        meta_frame.setObjectName("auditDetailMeta")
        grid = QGridLayout(meta_frame)
        grid.setSpacing(8)

        rec = self._record

        meta_fields = [
            ("رقم السجل:", str(rec.get("id", ""))),
            ("الجدول:", TABLE_LABELS.get(
                rec.get("table_name", ""), rec.get("table_name", "")
            )),
            ("العملية:", ACTION_LABELS.get(
                rec.get("action_type", ""), rec.get("action_type", "")
            )),
            ("رقم الصف:", str(rec.get("record_id", ""))),
            ("التاريخ:", (
                rec.get("action_timestamp").strftime("%Y-%m-%d %H:%M:%S")
                if rec.get("action_timestamp") else ""
            )),
            ("المستخدم:", rec.get("app_user") or rec.get("db_user", "")),
        ]

        for i, (label, value) in enumerate(meta_fields):
            row_i = i // 3
            col_i = (i % 3) * 2

            lbl = QLabel(label)
            lbl.setFont(cairo_bold)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(lbl, row_i, col_i)

            val = QLabel(str(value))
            val.setFont(cairo)
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(val, row_i, col_i + 1)

        layout.addWidget(meta_frame)

        # Changed fields
        changed = rec.get("changed_fields") or []
        if changed:
            changed_lbl = QLabel(f"الحقول المتغيرة:  {', '.join(changed)}")
            changed_lbl.setFont(cairo)
            changed_lbl.setWordWrap(True)
            layout.addWidget(changed_lbl)

        # Old vs New splitter
        splitter = QSplitter(Qt.Horizontal)

        # Old data
        old_frame = self._make_data_panel(
            "القيم القديمة  (Before)", rec.get("old_data")
        )
        splitter.addWidget(old_frame)

        # New data
        new_frame = self._make_data_panel(
            "القيم الجديدة  (After)", rec.get("new_data")
        )
        splitter.addWidget(new_frame)

        layout.addWidget(splitter, 1)

        # Close button
        close_btn = QPushButton("إغلاق")
        close_btn.setFont(get_font(FONT_SIZE_SMALL))
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _make_data_panel(
        self, title: str, data: Any
    ) -> QFrame:
        """Create a panel showing JSONB data."""
        frame = QFrame()
        frame.setObjectName("auditDataPanel")

        vl = QVBoxLayout(frame)
        vl.setContentsMargins(10, 10, 10, 10)
        vl.setSpacing(5)

        lbl = QLabel(title)
        lbl.setFont(get_font(FONT_SIZE_SMALL, FONT_WEIGHT_BOLD))
        lbl.setAlignment(Qt.AlignCenter)
        vl.addWidget(lbl)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        # Cross-platform monospace font (Rule 12)
        mono_font = QFont("Courier New", 9)
        mono_font.setStyleHint(QFont.Monospace)
        text_edit.setFont(mono_font)

        if data is None:
            text_edit.setPlainText("(لا توجد بيانات)")
        elif isinstance(data, dict):
            formatted = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            text_edit.setPlainText(formatted)
        else:
            text_edit.setPlainText(str(data))

        vl.addWidget(text_edit, 1)

        return frame
