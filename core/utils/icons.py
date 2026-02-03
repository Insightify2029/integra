"""
Icons Manager
=============
Centralized icon management using QtAwesome.
Provides 6000+ professional icons from Font Awesome, Material Design, etc.

Usage:
    from core.utils import Icons, icon

    # Using predefined icons
    button.setIcon(Icons.SAVE)
    button.setIcon(Icons.USER)

    # Using icon() function for custom icons
    button.setIcon(icon('fa5s.trash', color='red'))

    # With animation (spinner)
    button.setIcon(icon('fa5s.spinner', animation='spin'))
"""

from typing import Optional, Dict, Any
from PyQt5.QtGui import QIcon

try:
    import qtawesome as qta
    QTAWESOME_AVAILABLE = True
except ImportError:
    QTAWESOME_AVAILABLE = False

from core.logging import app_logger


# Default colors for INTEGRA theme
COLORS = {
    'primary': '#2563eb',      # Blue
    'success': '#10b981',      # Green
    'danger': '#ef4444',       # Red
    'warning': '#f59e0b',      # Orange
    'info': '#3b82f6',         # Light Blue
    'default': '#6b7280',      # Gray
    'dark': '#374151',         # Dark Gray
    'light': '#9ca3af',        # Light Gray
}


def icon(name: str, color: Optional[str] = None, scale: float = 1.0,
         animation: Optional[str] = None, **kwargs) -> QIcon:
    """
    Get an icon by name with optional customization.

    Args:
        name: Icon name (e.g., 'fa5s.save', 'mdi.account', 'ph.user')
        color: Icon color (hex or named color)
        scale: Scale factor (default 1.0)
        animation: Animation type ('spin', 'pulse', None)
        **kwargs: Additional qtawesome options

    Returns:
        QIcon object

    Icon Prefixes:
        fa5s: Font Awesome 5 Solid
        fa5b: Font Awesome 5 Brands
        mdi: Material Design Icons
        ph: Phosphor Icons
        ri: Remix Icons
        ei: Evil Icons

    Examples:
        icon('fa5s.save')                    # Simple icon
        icon('fa5s.user', color='#3498db')   # Colored icon
        icon('mdi.loading', animation='spin') # Animated icon
    """
    if not QTAWESOME_AVAILABLE:
        app_logger.warning(f"QtAwesome not available. Icon '{name}' not loaded.")
        return QIcon()

    try:
        options: Dict[str, Any] = {}

        if color:
            # Check if it's a named color
            if color in COLORS:
                options['color'] = COLORS[color]
            else:
                options['color'] = color

        if scale != 1.0:
            options['scale_factor'] = scale

        if animation == 'spin':
            options['animation'] = qta.Spin(None)
        elif animation == 'pulse':
            options['animation'] = qta.Pulse(None)

        options.update(kwargs)

        return qta.icon(name, **options)

    except Exception as e:
        app_logger.error(f"Failed to load icon '{name}': {e}")
        return QIcon()


def get_icon(name: str, color: Optional[str] = None) -> QIcon:
    """Alias for icon() function."""
    return icon(name, color)


class Icons:
    """
    Predefined icons for common actions.
    Use these for consistency across the application.

    Usage:
        from core.utils import Icons
        button.setIcon(Icons.SAVE)
    """

    # File Operations
    SAVE = property(lambda self: icon('fa5s.save', color='primary'))
    SAVE_AS = property(lambda self: icon('fa5s.file-export', color='primary'))
    OPEN = property(lambda self: icon('fa5s.folder-open', color='warning'))
    NEW = property(lambda self: icon('fa5s.file', color='info'))
    DELETE = property(lambda self: icon('fa5s.trash-alt', color='danger'))
    PRINT = property(lambda self: icon('fa5s.print', color='default'))
    EXPORT = property(lambda self: icon('fa5s.file-export', color='success'))
    IMPORT = property(lambda self: icon('fa5s.file-import', color='info'))

    # Navigation
    HOME = property(lambda self: icon('fa5s.home', color='primary'))
    BACK = property(lambda self: icon('fa5s.arrow-left', color='default'))
    FORWARD = property(lambda self: icon('fa5s.arrow-right', color='default'))
    UP = property(lambda self: icon('fa5s.arrow-up', color='default'))
    DOWN = property(lambda self: icon('fa5s.arrow-down', color='default'))
    REFRESH = property(lambda self: icon('fa5s.sync-alt', color='info'))
    MENU = property(lambda self: icon('fa5s.bars', color='default'))

    # Actions
    ADD = property(lambda self: icon('fa5s.plus', color='success'))
    EDIT = property(lambda self: icon('fa5s.edit', color='warning'))
    COPY = property(lambda self: icon('fa5s.copy', color='info'))
    CUT = property(lambda self: icon('fa5s.cut', color='warning'))
    PASTE = property(lambda self: icon('fa5s.paste', color='info'))
    SEARCH = property(lambda self: icon('fa5s.search', color='primary'))
    FILTER = property(lambda self: icon('fa5s.filter', color='info'))
    SORT = property(lambda self: icon('fa5s.sort', color='default'))
    CLOSE = property(lambda self: icon('fa5s.times', color='danger'))
    CHECK = property(lambda self: icon('fa5s.check', color='success'))
    CANCEL = property(lambda self: icon('fa5s.ban', color='danger'))

    # Users & People
    USER = property(lambda self: icon('fa5s.user', color='primary'))
    USERS = property(lambda self: icon('fa5s.users', color='primary'))
    USER_ADD = property(lambda self: icon('fa5s.user-plus', color='success'))
    USER_EDIT = property(lambda self: icon('fa5s.user-edit', color='warning'))
    USER_DELETE = property(lambda self: icon('fa5s.user-minus', color='danger'))
    PROFILE = property(lambda self: icon('fa5s.id-card', color='info'))

    # Business
    COMPANY = property(lambda self: icon('fa5s.building', color='primary'))
    DEPARTMENT = property(lambda self: icon('fa5s.sitemap', color='info'))
    MONEY = property(lambda self: icon('fa5s.money-bill-wave', color='success'))
    CALCULATOR = property(lambda self: icon('fa5s.calculator', color='info'))
    CHART = property(lambda self: icon('fa5s.chart-bar', color='primary'))
    CHART_LINE = property(lambda self: icon('fa5s.chart-line', color='success'))
    CHART_PIE = property(lambda self: icon('fa5s.chart-pie', color='warning'))
    CALENDAR = property(lambda self: icon('fa5s.calendar-alt', color='info'))
    CLOCK = property(lambda self: icon('fa5s.clock', color='warning'))
    BRIEFCASE = property(lambda self: icon('fa5s.briefcase', color='default'))

    # Status
    SUCCESS = property(lambda self: icon('fa5s.check-circle', color='success'))
    ERROR = property(lambda self: icon('fa5s.times-circle', color='danger'))
    WARNING = property(lambda self: icon('fa5s.exclamation-triangle', color='warning'))
    INFO = property(lambda self: icon('fa5s.info-circle', color='info'))
    QUESTION = property(lambda self: icon('fa5s.question-circle', color='primary'))
    LOADING = property(lambda self: icon('fa5s.spinner', color='primary', animation='spin'))

    # Settings
    SETTINGS = property(lambda self: icon('fa5s.cog', color='default'))
    TOOLS = property(lambda self: icon('fa5s.tools', color='default'))
    KEY = property(lambda self: icon('fa5s.key', color='warning'))
    LOCK = property(lambda self: icon('fa5s.lock', color='danger'))
    UNLOCK = property(lambda self: icon('fa5s.unlock', color='success'))
    SHIELD = property(lambda self: icon('fa5s.shield-alt', color='primary'))

    # Data
    DATABASE = property(lambda self: icon('fa5s.database', color='primary'))
    TABLE = property(lambda self: icon('fa5s.table', color='info'))
    LIST = property(lambda self: icon('fa5s.list', color='default'))
    GRID = property(lambda self: icon('fa5s.th', color='default'))
    FILE_EXCEL = property(lambda self: icon('fa5s.file-excel', color='success'))
    FILE_PDF = property(lambda self: icon('fa5s.file-pdf', color='danger'))
    FILE_WORD = property(lambda self: icon('fa5s.file-word', color='primary'))

    # Communication
    EMAIL = property(lambda self: icon('fa5s.envelope', color='primary'))
    PHONE = property(lambda self: icon('fa5s.phone', color='success'))
    COMMENT = property(lambda self: icon('fa5s.comment', color='info'))
    BELL = property(lambda self: icon('fa5s.bell', color='warning'))

    # AI
    AI = property(lambda self: icon('fa5s.robot', color='primary'))
    BRAIN = property(lambda self: icon('fa5s.brain', color='info'))
    MAGIC = property(lambda self: icon('fa5s.magic', color='warning'))

    # Misc
    STAR = property(lambda self: icon('fa5s.star', color='warning'))
    HEART = property(lambda self: icon('fa5s.heart', color='danger'))
    FLAG = property(lambda self: icon('fa5s.flag', color='danger'))
    TAG = property(lambda self: icon('fa5s.tag', color='info'))
    LINK = property(lambda self: icon('fa5s.link', color='primary'))
    DOWNLOAD = property(lambda self: icon('fa5s.download', color='success'))
    UPLOAD = property(lambda self: icon('fa5s.upload', color='info'))
    CLOUD = property(lambda self: icon('fa5s.cloud', color='info'))
    SYNC = property(lambda self: icon('fa5s.sync', color='primary'))
    POWER = property(lambda self: icon('fa5s.power-off', color='danger'))


# Singleton instance
_icons_instance: Optional[Icons] = None


def get_icons() -> Icons:
    """Get the global Icons instance."""
    global _icons_instance
    if _icons_instance is None:
        _icons_instance = Icons()
    return _icons_instance


# For convenience, create a module-level Icons instance
# Usage: from core.utils.icons import Icons; button.setIcon(Icons.SAVE)
Icons = get_icons()
