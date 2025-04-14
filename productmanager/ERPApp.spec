# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('erp/assets', 'assets'), ('erp/icons', 'icons'), ('erp/ui', 'ui'), ('erp/services', 'services'), ('erp/config.py', '.')]
binaries = []
hiddenimports = ['requests', 'pandas', 'folium', 'PyQt5.QtChart', 'PyQt5.QtPrintSupport', 'PyQt5.QtWebEngineWidgets', 'sip', '_cffi_backend', 'sklearn.utils._heap', 'sklearn.utils._sorting', 'sklearn.utils._typedefs', 'sklearn.utils._cython_blas', 'scipy._lib._fpumode']
hiddenimports += collect_submodules('PyQt5.QtChart')
hiddenimports += collect_submodules('sklearn')
hiddenimports += collect_submodules('scipy')
hiddenimports += collect_submodules('charset_normalizer')
tmp_ret = collect_all('torch')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['erp\\main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
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
