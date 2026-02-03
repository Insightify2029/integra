# -*- mode: python ; coding: utf-8 -*-
"""
INTEGRA - PyInstaller Specification File
========================================
ملف إعدادات بناء الملف التنفيذي

الاستخدام:
    pyinstaller INTEGRA.spec

أو استخدم build.py للتسهيل
"""

import os
import sys

# المسار الأساسي للمشروع
BASE_PATH = os.path.dirname(os.path.abspath(SPEC))

# تحليل الملف الرئيسي
a = Analysis(
    ['main.py'],
    pathex=[BASE_PATH],
    binaries=[],
    datas=[
        # الموارد
        ('resources', 'resources'),
        # ملفات الإعدادات
        ('sync_settings.json', '.'),
    ],
    hiddenimports=[
        # PyQt5
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        # Database
        'psycopg2',
        'psycopg2.extensions',
        'psycopg2.extras',
        # Logging
        'loguru',
        # Core modules
        'core',
        'core.config',
        'core.database',
        'core.logging',
        'core.error_handling',
        'core.threading',
        'core.sync',
        'core.themes',
        # UI modules
        'ui',
        'ui.windows',
        'ui.dialogs',
        'ui.components',
        # Business modules
        'modules',
        'modules.mostahaqat',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # استبعاد المكتبات غير الضرورية لتقليل الحجم
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter',
        'unittest',
        'test',
        'tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# تجميع الملفات
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None
)

# بناء الملف التنفيذي
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='INTEGRA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # ضغط لتقليل الحجم
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # بدون نافذة console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/integra.ico',  # الأيقونة
    version='version_info.txt' if os.path.exists('version_info.txt') else None,
)
