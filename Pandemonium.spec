# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('c:\\Code\\Pandemonium\\resources\\enemies\\enemies_data', 'resources/enemies/enemies_data'), ('c:\\Code\\Pandemonium\\resources\\skill_book', 'resources/skill_book'), ('c:\\Code\\Pandemonium\\gui', 'gui')],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.font', 'tkinter.messagebox', 'yaml'],
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
    name='Pandemonium',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='Pandemonium',
)
