# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['requests', 'pandas', 'PyQt5.QtChart', 'PyQt5.QtPrintSupport', 'folium', 'PyQt5.QtWebEngineWidgets']
hiddenimports += collect_submodules('PyQt5.QtChart')


a = Analysis(
    ['erp\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('erp/assets', 'assets'), ('erp/icons', 'icons'), ('erp/ui', 'ui'), ('erp/services', 'services'), ('erp/config.py', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ERPApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ERPApp',
)
