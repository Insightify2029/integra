# -*- coding: utf-8 -*-
"""
Sync Configuration
==================
تحميل وحفظ إعدادات المزامنة
"""

import json
from pathlib import Path


# ملف الإعدادات في مجلد المشروع
_CONFIG_FILE = Path(__file__).parent.parent.parent / "sync_settings.json"

# الإعدادات الافتراضية
_DEFAULTS = {
    "sync_on_startup": True,
    "sync_on_exit": True,
    "auto_sync_enabled": False,
    "auto_sync_interval_minutes": 30,
    "last_sync_time": "",
    "last_sync_direction": ""
}


def load_sync_config() -> dict:
    """تحميل إعدادات المزامنة."""
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            return {**_DEFAULTS, **config}
        except Exception:
            pass
    return dict(_DEFAULTS)


def save_sync_config(config: dict) -> bool:
    """حفظ إعدادات المزامنة."""
    try:
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False
