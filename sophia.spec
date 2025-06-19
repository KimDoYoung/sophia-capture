# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\sophia.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\PC\\work\\sophia-capture\\.venv\\Lib\\site-packages\\PySide6\\plugins/platforms', 'platforms')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='sophia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\PC\\work\\sophia-capture\\src\\sophia_capture.ico'],
)
