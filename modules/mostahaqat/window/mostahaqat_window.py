"""
Mostahaqat Window
=================
Main window for the Mostahaqat module.
Professional clean interface with powerful menus and toolbars.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QAction, QToolBar,
    QFrame, QStackedWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.windows.base import BaseWindow
from ui.components.notifications import toast_info

# Import new screens
from modules.mostahaqat.screens import EmployeesListScreen, EmployeeProfileScreen, EditEmployeeScreen


class MostahaqatWindow(BaseWindow):
    """
    Mostahaqat module main window.
    Clean professional interface - data accessed via menus/tools.
    """
    
    def __init__(self):
        super().__init__(title_suffix="مستحقات العاملين")
        
        # Stack widget to switch between screens
        self._stack = None
        self._welcome_screen = None
        self._employees_list_screen = None
        self._employee_profile_screen = None
        self._edit_employee_screen = None
        
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_central_area()
        self._setup_statusbar()
    
    def _setup_menubar(self):
        """Setup comprehensive menu bar."""
        menubar = self.menuBar()
        
        # ═══════════════════════════════════════════════════════
        # 👥 الموظفين
        # ═══════════════════════════════════════════════════════
        employees_menu = menubar.addMenu("👥 الموظفين")
        
        # عرض
        view_menu = employees_menu.addMenu("📋 عرض")
        view_menu.addAction(self._create_action("جميع الموظفين", "Ctrl+Shift+A", self._show_all_employees))
        view_menu.addAction(self._create_action("الموظفين النشطين", "Ctrl+Shift+E", self._show_active_employees))
        view_menu.addAction(self._create_action("الموظفين المنتهية عقودهم", "", self._show_terminated))
        view_menu.addSeparator()
        view_menu.addAction(self._create_action("حسب القسم", "", self._show_by_department))
        view_menu.addAction(self._create_action("حسب الجنسية", "", self._show_by_nationality))
        view_menu.addAction(self._create_action("حسب الوظيفة", "", self._show_by_job))
        
        employees_menu.addSeparator()
        
        # إضافة
        employees_menu.addAction(self._create_action("➕ إضافة موظف جديد", "Ctrl+N", self._add_employee))
        employees_menu.addAction(self._create_action("📝 تعديل بيانات موظف", "Ctrl+E", self._edit_employee))
        employees_menu.addAction(self._create_action("🔍 البحث عن موظف", "Ctrl+F", self._search_employee))
        
        employees_menu.addSeparator()
        
        # استيراد/تصدير
        import_menu = employees_menu.addMenu("📥 استيراد/تصدير")
        import_menu.addAction(self._create_action("استيراد من Excel", "", self._import_excel))
        import_menu.addAction(self._create_action("تصدير إلى Excel", "", self._export_excel))
        import_menu.addAction(self._create_action("تصدير إلى PDF", "", self._export_pdf))
        
        # ═══════════════════════════════════════════════════════
        # 💰 المستحقات
        # ═══════════════════════════════════════════════════════
        benefits_menu = menubar.addMenu("💰 المستحقات")
        
        # الرواتب
        salary_menu = benefits_menu.addMenu("💵 الرواتب")
        salary_menu.addAction(self._create_action("عرض الرواتب", "", self._show_salaries))
        salary_menu.addAction(self._create_action("تعديل الراتب", "", self._edit_salary))
        salary_menu.addAction(self._create_action("سجل تعديلات الرواتب", "", self._salary_history))
        
        benefits_menu.addSeparator()
        
        # البدلات
        allowances_menu = benefits_menu.addMenu("🎁 البدلات")
        allowances_menu.addAction(self._create_action("بدل السكن", "", self._housing_allowance))
        allowances_menu.addAction(self._create_action("بدل النقل", "", self._transport_allowance))
        allowances_menu.addAction(self._create_action("بدلات أخرى", "", self._other_allowances))
        
        benefits_menu.addSeparator()
        
        # الخصومات
        deductions_menu = benefits_menu.addMenu("➖ الخصومات")
        deductions_menu.addAction(self._create_action("خصم الغياب", "", self._absence_deduction))
        deductions_menu.addAction(self._create_action("خصم التأخير", "", self._late_deduction))
        deductions_menu.addAction(self._create_action("خصومات أخرى", "", self._other_deductions))
        
        # ═══════════════════════════════════════════════════════
        # 🏖️ الإجازات
        # ═══════════════════════════════════════════════════════
        leave_menu = menubar.addMenu("🏖️ الإجازات")
        
        leave_menu.addAction(self._create_action("📊 أرصدة الإجازات", "Ctrl+L", self._leave_balances))
        leave_menu.addAction(self._create_action("➕ تسجيل إجازة", "", self._add_leave))
        leave_menu.addAction(self._create_action("📋 سجل الإجازات", "", self._leave_history))
        
        leave_menu.addSeparator()
        
        # تسوية
        settlement_menu = leave_menu.addMenu("💵 تسوية الإجازات")
        settlement_menu.addAction(self._create_action("حساب تسوية فردية", "", self._single_settlement))
        settlement_menu.addAction(self._create_action("حساب تسوية جماعية", "", self._bulk_settlement))
        settlement_menu.addAction(self._create_action("تقرير التسويات", "", self._settlement_report))
        
        # ═══════════════════════════════════════════════════════
        # ⏰ الإضافي
        # ═══════════════════════════════════════════════════════
        overtime_menu = menubar.addMenu("⏰ الإضافي")
        
        overtime_menu.addAction(self._create_action("📊 ملخص الإضافي الشهري", "Ctrl+O", self._overtime_summary))
        overtime_menu.addAction(self._create_action("➕ تسجيل ساعات إضافية", "", self._add_overtime))
        overtime_menu.addAction(self._create_action("📋 سجل الإضافي", "", self._overtime_history))
        
        overtime_menu.addSeparator()
        
        overtime_menu.addAction(self._create_action("⚙️ إعدادات الإضافي", "", self._overtime_settings))
        
        # ═══════════════════════════════════════════════════════
        # 🚪 نهاية الخدمة
        # ═══════════════════════════════════════════════════════
        eos_menu = menubar.addMenu("🚪 نهاية الخدمة")
        
        eos_menu.addAction(self._create_action("🧮 حاسبة نهاية الخدمة", "Ctrl+Shift+E", self._eos_calculator))
        eos_menu.addAction(self._create_action("📋 المستقيلين", "", self._resigned_employees))
        eos_menu.addAction(self._create_action("📊 تقرير نهاية الخدمة", "", self._eos_report))
        
        eos_menu.addSeparator()
        
        eos_menu.addAction(self._create_action("⚙️ إعدادات نهاية الخدمة", "", self._eos_settings))
        
        # ═══════════════════════════════════════════════════════
        # 📊 التقارير
        # ═══════════════════════════════════════════════════════
        reports_menu = menubar.addMenu("📊 التقارير")
        
        # تقارير الموظفين
        emp_reports = reports_menu.addMenu("👥 تقارير الموظفين")
        emp_reports.addAction(self._create_action("قائمة الموظفين", "", self._report_employees_list))
        emp_reports.addAction(self._create_action("توزيع الجنسيات", "", self._report_nationalities))
        emp_reports.addAction(self._create_action("توزيع الأقسام", "", self._report_departments))
        emp_reports.addAction(self._create_action("توزيع الوظائف", "", self._report_jobs))
        
        # تقارير مالية
        fin_reports = reports_menu.addMenu("💰 تقارير مالية")
        fin_reports.addAction(self._create_action("كشف الرواتب", "", self._report_payroll))
        fin_reports.addAction(self._create_action("ملف البنك (WPS)", "", self._report_wps))
        fin_reports.addAction(self._create_action("تقرير البدلات", "", self._report_allowances))
        fin_reports.addAction(self._create_action("تقرير الخصومات", "", self._report_deductions))
        
        reports_menu.addSeparator()
        
        reports_menu.addAction(self._create_action("📝 تقرير مخصص", "", self._custom_report))
        
        # ═══════════════════════════════════════════════════════
        # ⚙️ الإعدادات
        # ═══════════════════════════════════════════════════════
        settings_menu = menubar.addMenu("⚙️ الإعدادات")
        
        # البيانات الأساسية
        master_menu = settings_menu.addMenu("📚 البيانات الأساسية")
        master_menu.addAction(self._create_action("الجنسيات", "", self._manage_nationalities))
        master_menu.addAction(self._create_action("الأقسام", "", self._manage_departments))
        master_menu.addAction(self._create_action("الوظائف", "", self._manage_jobs))
        master_menu.addAction(self._create_action("البنوك", "", self._manage_banks))
        master_menu.addAction(self._create_action("الشركات", "", self._manage_companies))
        
        settings_menu.addSeparator()
        
        settings_menu.addAction(self._create_action("⚙️ إعدادات الموديول", "", self._module_settings))
    
    def _setup_toolbar(self):
        """Setup main toolbar with quick actions."""
        toolbar = QToolBar("الأدوات الرئيسية")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #1e293b;
                border: none;
                padding: 8px;
                spacing: 5px;
            }
            QToolBar QToolButton {
                background-color: #334155;
                color: #f1f5f9;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QToolBar QToolButton:hover {
                background-color: #475569;
            }
            QToolBar QToolButton:pressed {
                background-color: #2563eb;
            }
            QToolBar::separator {
                width: 1px;
                background-color: #475569;
                margin: 0 10px;
            }
        """)
        
        # Quick actions
        toolbar.addAction(self._create_action("👥 الموظفين", "", self._show_all_employees))
        toolbar.addAction(self._create_action("➕ إضافة", "", self._add_employee))
        toolbar.addAction(self._create_action("🔍 بحث", "", self._search_employee))
        toolbar.addSeparator()
        toolbar.addAction(self._create_action("🏖️ تسوية إجازة", "", self._single_settlement))
        toolbar.addAction(self._create_action("⏰ إضافي", "", self._overtime_summary))
        toolbar.addAction(self._create_action("🚪 نهاية خدمة", "", self._eos_calculator))
        toolbar.addSeparator()
        toolbar.addAction(self._create_action("📊 تقارير", "", self._reports_menu))
        
        self.addToolBar(toolbar)
    
    def _setup_central_area(self):
        """Setup central area with stacked widget."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Stacked widget for switching screens
        self._stack = QStackedWidget()
        
        # Welcome screen (index 0)
        self._welcome_screen = self._create_welcome_screen()
        self._stack.addWidget(self._welcome_screen)
        
        # Employees list screen (index 1)
        self._employees_list_screen = EmployeesListScreen()
        self._employees_list_screen.employee_selected.connect(self._open_employee_profile)
        self._employees_list_screen.add_employee_clicked.connect(self._add_employee)
        self._stack.addWidget(self._employees_list_screen)
        
        # Employee profile screen (index 2)
        self._employee_profile_screen = EmployeeProfileScreen()
        self._employee_profile_screen.back_clicked.connect(self._show_employees_list)
        self._employee_profile_screen.edit_clicked.connect(self._edit_employee_data)
        self._employee_profile_screen.leave_settlement_clicked.connect(self._employee_leave_settlement)
        self._employee_profile_screen.overtime_clicked.connect(self._employee_overtime)
        self._employee_profile_screen.end_of_service_clicked.connect(self._employee_eos)
        self._employee_profile_screen.deactivate_clicked.connect(self._deactivate_employee)
        self._stack.addWidget(self._employee_profile_screen)
        
        # Edit employee (3)
        self._edit_employee_screen = EditEmployeeScreen()
        self._edit_employee_screen.saved.connect(self._on_employee_saved)
        self._edit_employee_screen.cancelled.connect(self._on_edit_cancelled)
        self._stack.addWidget(self._edit_employee_screen)
        
        layout.addWidget(self._stack)
    
    def _create_welcome_screen(self) -> QWidget:
        """Create welcome screen widget."""
        workspace = QFrame()
        workspace.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
            }
        """)
        
        ws_layout = QVBoxLayout(workspace)
        ws_layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title = QLabel("مستحقات العاملين")
        title.setFont(QFont("Cairo", 36, QFont.Bold))
        title.setStyleSheet("color: #38bdf8; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        ws_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("اختر من القائمة أو شريط الأدوات للبدء")
        subtitle.setFont(QFont("Cairo", 14))
        subtitle.setStyleSheet("color: #64748b; background: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        ws_layout.addWidget(subtitle)
        
        return workspace
    
    def _setup_statusbar(self):
        """Setup status bar."""
        status = self.statusBar()
        status.setStyleSheet("""
            QStatusBar {
                background-color: #1e293b;
                color: #94a3b8;
                border-top: 1px solid #334155;
                padding: 5px;
            }
        """)
        status.showMessage("جاهز")
    
    def _create_action(self, text, shortcut, slot):
        """Create a menu/toolbar action."""
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        return action
    
    # ═══════════════════════════════════════════════════════════════
    # Navigation Methods
    # ═══════════════════════════════════════════════════════════════
    
    def _show_welcome(self):
        """Show welcome screen."""
        self._stack.setCurrentIndex(0)
        self.statusBar().showMessage("جاهز")
    
    def _show_employees_list(self):
        """Show employees list screen."""
        self._employees_list_screen.refresh()
        self._stack.setCurrentIndex(1)
        self.statusBar().showMessage("عرض قائمة الموظفين")
    
    def _open_employee_profile(self, employee_data: dict):
        """Open employee profile screen."""
        self._employee_profile_screen.set_employee(employee_data)
        self._stack.setCurrentIndex(2)
        self.statusBar().showMessage(f"ملف الموظف: {employee_data.get('name_ar', '')}")
    
    # ═══════════════════════════════════════════════════════════════
    # Employee Actions (from profile screen)
    # ═══════════════════════════════════════════════════════════════
    
    def _edit_employee_data(self, employee: dict):
        """Edit employee data."""
        toast_info(self, "تعديل", f"تعديل بيانات {employee.get('name_ar', '')} - قيد التطوير")
    
    def _employee_leave_settlement(self, employee: dict):
        """Calculate leave settlement for employee."""
        toast_info(self, "تسوية إجازة", f"تسوية إجازة {employee.get('name_ar', '')} - قيد التطوير")
    
    def _employee_overtime(self, employee: dict):
        """Calculate overtime for employee."""
        toast_info(self, "حساب الإضافي", f"حساب الإضافي لـ {employee.get('name_ar', '')} - قيد التطوير")
    
    def _employee_eos(self, employee: dict):
        """Calculate end of service for employee."""
        toast_info(self, "نهاية الخدمة", f"حساب نهاية خدمة {employee.get('name_ar', '')} - قيد التطوير")
    
    def _deactivate_employee(self, employee: dict):
        """Deactivate employee."""
        toast_info(self, "إيقاف", f"إيقاف الموظف {employee.get('name_ar', '')} - قيد التطوير")
    
    # ═══════════════════════════════════════════════════════════════
    # Menu Action Handlers
    # ═══════════════════════════════════════════════════════════════
    
    def _on_employee_saved(self, updated_data: dict):
        """بعد حفظ التعديلات - يرجع لملف الموظف."""
        self._employee_profile_screen.set_employee(updated_data)
        self._stack.setCurrentIndex(2)
        self.statusBar().showMessage(f"\u2705 تم حفظ: {updated_data.get('name_ar', '')}")

    def _on_edit_cancelled(self):
        """إلغاء التعديل - يرجع لملف الموظف."""
        self._stack.setCurrentIndex(2)
        self.statusBar().showMessage("تم إلغاء التعديل")

    def _show_all_employees(self):
        """Show all employees - NOW WORKING!"""
        self._show_employees_list()
    
    def _show_active_employees(self):
        toast_info(self, "الموظفين", "عرض الموظفين النشطين - قيد التطوير")
    
    def _show_terminated(self):
        toast_info(self, "الموظفين", "عرض المنتهية عقودهم - قيد التطوير")
    
    def _show_by_department(self):
        toast_info(self, "الموظفين", "عرض حسب القسم - قيد التطوير")
    
    def _show_by_nationality(self):
        toast_info(self, "الموظفين", "عرض حسب الجنسية - قيد التطوير")
    
    def _show_by_job(self):
        toast_info(self, "الموظفين", "عرض حسب الوظيفة - قيد التطوير")
    
    def _add_employee(self):
        toast_info(self, "إضافة", "إضافة موظف جديد - قيد التطوير")
    
    def _edit_employee(self):
        toast_info(self, "تعديل", "تعديل بيانات موظف - قيد التطوير")
    
    def _search_employee(self):
        toast_info(self, "بحث", "البحث عن موظف - قيد التطوير")
    
    def _import_excel(self):
        toast_info(self, "استيراد", "استيراد من Excel - قيد التطوير")
    
    def _export_excel(self):
        toast_info(self, "تصدير", "تصدير إلى Excel - قيد التطوير")
    
    def _export_pdf(self):
        toast_info(self, "تصدير", "تصدير إلى PDF - قيد التطوير")
    
    def _show_salaries(self):
        toast_info(self, "الرواتب", "عرض الرواتب - قيد التطوير")
    
    def _edit_salary(self):
        toast_info(self, "الرواتب", "تعديل الراتب - قيد التطوير")
    
    def _salary_history(self):
        toast_info(self, "الرواتب", "سجل تعديلات الرواتب - قيد التطوير")
    
    def _housing_allowance(self):
        toast_info(self, "البدلات", "بدل السكن - قيد التطوير")
    
    def _transport_allowance(self):
        toast_info(self, "البدلات", "بدل النقل - قيد التطوير")
    
    def _other_allowances(self):
        toast_info(self, "البدلات", "بدلات أخرى - قيد التطوير")
    
    def _absence_deduction(self):
        toast_info(self, "الخصومات", "خصم الغياب - قيد التطوير")
    
    def _late_deduction(self):
        toast_info(self, "الخصومات", "خصم التأخير - قيد التطوير")
    
    def _other_deductions(self):
        toast_info(self, "الخصومات", "خصومات أخرى - قيد التطوير")
    
    def _leave_balances(self):
        toast_info(self, "الإجازات", "أرصدة الإجازات - قيد التطوير")
    
    def _add_leave(self):
        toast_info(self, "الإجازات", "تسجيل إجازة - قيد التطوير")
    
    def _leave_history(self):
        toast_info(self, "الإجازات", "سجل الإجازات - قيد التطوير")
    
    def _single_settlement(self):
        toast_info(self, "تسوية", "حساب تسوية فردية - قيد التطوير")
    
    def _bulk_settlement(self):
        toast_info(self, "تسوية", "حساب تسوية جماعية - قيد التطوير")
    
    def _settlement_report(self):
        toast_info(self, "تسوية", "تقرير التسويات - قيد التطوير")
    
    def _overtime_summary(self):
        toast_info(self, "الإضافي", "ملخص الإضافي الشهري - قيد التطوير")
    
    def _add_overtime(self):
        toast_info(self, "الإضافي", "تسجيل ساعات إضافية - قيد التطوير")
    
    def _overtime_history(self):
        toast_info(self, "الإضافي", "سجل الإضافي - قيد التطوير")
    
    def _overtime_settings(self):
        toast_info(self, "الإضافي", "إعدادات الإضافي - قيد التطوير")
    
    def _eos_calculator(self):
        toast_info(self, "نهاية الخدمة", "حاسبة نهاية الخدمة - قيد التطوير")
    
    def _resigned_employees(self):
        toast_info(self, "نهاية الخدمة", "المستقيلين - قيد التطوير")
    
    def _eos_report(self):
        toast_info(self, "نهاية الخدمة", "تقرير نهاية الخدمة - قيد التطوير")
    
    def _eos_settings(self):
        toast_info(self, "نهاية الخدمة", "إعدادات نهاية الخدمة - قيد التطوير")
    
    def _report_employees_list(self):
        toast_info(self, "التقارير", "قائمة الموظفين - قيد التطوير")
    
    def _report_nationalities(self):
        toast_info(self, "التقارير", "توزيع الجنسيات - قيد التطوير")
    
    def _report_departments(self):
        toast_info(self, "التقارير", "توزيع الأقسام - قيد التطوير")
    
    def _report_jobs(self):
        toast_info(self, "التقارير", "توزيع الوظائف - قيد التطوير")
    
    def _report_payroll(self):
        toast_info(self, "التقارير", "كشف الرواتب - قيد التطوير")
    
    def _report_wps(self):
        toast_info(self, "التقارير", "ملف البنك WPS - قيد التطوير")
    
    def _report_allowances(self):
        toast_info(self, "التقارير", "تقرير البدلات - قيد التطوير")
    
    def _report_deductions(self):
        toast_info(self, "التقارير", "تقرير الخصومات - قيد التطوير")
    
    def _custom_report(self):
        toast_info(self, "التقارير", "تقرير مخصص - قيد التطوير")
    
    def _manage_nationalities(self):
        toast_info(self, "الإعدادات", "إدارة الجنسيات - قيد التطوير")
    
    def _manage_departments(self):
        toast_info(self, "الإعدادات", "إدارة الأقسام - قيد التطوير")
    
    def _manage_jobs(self):
        toast_info(self, "الإعدادات", "إدارة الوظائف - قيد التطوير")
    
    def _manage_banks(self):
        toast_info(self, "الإعدادات", "إدارة البنوك - قيد التطوير")
    
    def _manage_companies(self):
        toast_info(self, "الإعدادات", "إدارة الشركات - قيد التطوير")
    
    def _module_settings(self):
        toast_info(self, "الإعدادات", "إعدادات الموديول - قيد التطوير")
    
    def _reports_menu(self):
        toast_info(self, "التقارير", "قائمة التقارير - قيد التطوير")