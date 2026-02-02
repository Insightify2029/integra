# -*- coding: utf-8 -*-
"""Sync Configuration v3 - تحميل وحفظ إعدادات المزامنة"""

import json
from pathlib import Path

_CONFIG_FILE = Path(__file__).parent.parent.parent / "sync_settings.json"

_DEFAULTS = {
    "sync_on_startup": True,
    "sync_on_exit_ask": True,
    "auto_sync_enabled": False,
    "auto_sync_interval_hours": 2,
    "last_sync_time": "",
    "last_sync_type": "",
    "backup_retention_days": 30,
}


def load_sync_config() -> dict:
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            return {**_DEFAULTS, **config}
        except Exception:
            pass
    return dict(_DEFAULTS)


def save_sync_config(config: dict) -> bool:
    try:
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def get_config_value(key: str, default=None):
    config = load_sync_config()
    return config.get(key, default if default is not None else _DEFAULTS.get(key))


def set_config_value(key: str, value) -> bool:
    config = load_sync_config()
    config[key] = value
    return save_sync_config(config)
