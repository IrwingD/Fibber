# -*- mode: python ; coding: utf-8 -*-
# Build with:  python -m PyInstaller build.spec --noconfirm
# Output:      dist/Fibber.exe   <-- this single file is the whole app
#
# NOTE: this is --onefile mode. Every launch silently self-extracts to a
# temp folder before running (adds ~1-3s startup), in exchange for
# shipping literally one file with nothing alongside it. If startup
# speed matters more than a single-file download, switch back to
# --onedir (see git history / ask for the onedir version of this spec).

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
    a.binaries,
    a.datas,
    [],
    name='Fibber',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # no terminal window pops up alongside the app
    disable_windowed_traceback=False,
    argv_emulation=False,
)