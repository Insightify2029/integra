"""
Master Data Management
======================
Professional forms for managing master/reference data:
- Nationalities (الجنسيات)
- Departments (الأقسام)
- Job Titles (الوظائف)
- Banks (البنوك)
- Companies (الشركات)
"""

from .master_data_window import MasterDataWindow
from .master_data_dialog import MasterDataDialog
from .import_dialog import ImportDialog
from .export_choice_dialog import ExportChoiceDialog

__all__ = [
    'MasterDataWindow',
    'MasterDataDialog',
    'ImportDialog',
    'ExportChoiceDialog',
]
