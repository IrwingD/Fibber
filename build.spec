# -*- mode: python ; coding: utf-8 -*-
# Build with:  pyinstaller build.spec --noconfirm
# Output:      dist/SyntheticDataStudio/   <-- this whole folder is the portable app

from PyInstaller.utils.hooks import collect_data_files

datas = [('static', 'static')]
datas += collect_data_files('faker')  # bundles Faker's per-locale word/name lists

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['faker_api'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SyntheticDataStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,      # no terminal window pops up alongside the app
    disable_windowed_traceback=False,
    argv_emulation=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SyntheticDataStudio',   # -> dist/SyntheticDataStudio/
)
