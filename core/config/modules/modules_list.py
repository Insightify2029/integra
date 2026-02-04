"""
Modules List
============
List of all available modules.
"""

from . import module_mostahaqat
from . import module_costing
from . import module_logistics
from . import module_custody
from . import module_insurance
from . import module_email
from . import module_designer
from . import module_calendar
from . import module_dashboard
from . import module_bi


def get_all_modules():
    """Get list of all modules."""
    return [
        {
            'id': module_mostahaqat.MODULE_ID,
            'name_ar': module_mostahaqat.MODULE_NAME_AR,
            'name_en': module_mostahaqat.MODULE_NAME_EN,
            'icon': module_mostahaqat.MODULE_ICON,
            'color': module_mostahaqat.MODULE_COLOR,
            'enabled': module_mostahaqat.MODULE_ENABLED
        },
        {
            'id': module_costing.MODULE_ID,
            'name_ar': module_costing.MODULE_NAME_AR,
            'name_en': module_costing.MODULE_NAME_EN,
            'icon': module_costing.MODULE_ICON,
            'color': module_costing.MODULE_COLOR,
            'enabled': module_costing.MODULE_ENABLED
        },
        {
            'id': module_logistics.MODULE_ID,
            'name_ar': module_logistics.MODULE_NAME_AR,
            'name_en': module_logistics.MODULE_NAME_EN,
            'icon': module_logistics.MODULE_ICON,
            'color': module_logistics.MODULE_COLOR,
            'enabled': module_logistics.MODULE_ENABLED
        },
        {
            'id': module_custody.MODULE_ID,
            'name_ar': module_custody.MODULE_NAME_AR,
            'name_en': module_custody.MODULE_NAME_EN,
            'icon': module_custody.MODULE_ICON,
            'color': module_custody.MODULE_COLOR,
            'enabled': module_custody.MODULE_ENABLED
        },
        {
            'id': module_insurance.MODULE_ID,
            'name_ar': module_insurance.MODULE_NAME_AR,
            'name_en': module_insurance.MODULE_NAME_EN,
            'icon': module_insurance.MODULE_ICON,
            'color': module_insurance.MODULE_COLOR,
            'enabled': module_insurance.MODULE_ENABLED
        },
        {
            'id': module_email.MODULE_ID,
            'name_ar': module_email.MODULE_NAME_AR,
            'name_en': module_email.MODULE_NAME_EN,
            'icon': module_email.MODULE_ICON,
            'color': module_email.MODULE_COLOR,
            'enabled': module_email.MODULE_ENABLED
        },
        {
            'id': module_designer.MODULE_ID,
            'name_ar': module_designer.MODULE_NAME_AR,
            'name_en': module_designer.MODULE_NAME_EN,
            'icon': module_designer.MODULE_ICON,
            'color': module_designer.MODULE_COLOR,
            'enabled': module_designer.MODULE_ENABLED
        },
        {
            'id': module_calendar.MODULE_ID,
            'name_ar': module_calendar.MODULE_NAME_AR,
            'name_en': module_calendar.MODULE_NAME_EN,
            'icon': module_calendar.MODULE_ICON,
            'color': module_calendar.MODULE_COLOR,
            'enabled': module_calendar.MODULE_ENABLED
        },
        {
            'id': module_dashboard.MODULE_ID,
            'name_ar': module_dashboard.MODULE_NAME_AR,
            'name_en': module_dashboard.MODULE_NAME_EN,
            'icon': module_dashboard.MODULE_ICON,
            'color': module_dashboard.MODULE_COLOR,
            'enabled': module_dashboard.MODULE_ENABLED
        },
        {
            'id': module_bi.MODULE_ID,
            'name_ar': module_bi.MODULE_NAME_AR,
            'name_en': module_bi.MODULE_NAME_EN,
            'icon': module_bi.MODULE_ICON,
            'color': module_bi.MODULE_COLOR,
            'enabled': module_bi.MODULE_ENABLED
        }
    ]


def get_enabled_modules():
    """Get list of enabled modules only."""
    return [m for m in get_all_modules() if m['enabled']]


def get_module_by_id(module_id):
    """Get module by its ID."""
    for module in get_all_modules():
        if module['id'] == module_id:
            return module
    return None
