# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('resources/style.qss', 'resources'),
           ('resources/app_icon2.png', 'resources'),
           ('resources/down_arrow.svg', 'resources'),
           ('resources/up_arrow.svg', 'resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6.QtPdf', 'PyQt6.QtNetwork', 'PyQt6.QtQuick',
              'PyQt6.QtQml', 'PyQt6.QtDesigner', 'PyQt6.QtBluetooth',
              'PyQt6.QtMultimedia', 'PyQt6.QtSensors', 'PyQt6.QtNfc',
              'PyQt6.QtSerialPort', 'PyQt6.QtTest', 'PyQt6.QtHelp',
              'PyQt6.QtWebChannel', 'PyQt6.QtWebSockets',
              'PyQt6.QtTextToSpeech', 'PyQt6.QtRemoteObjects',
              'PyQt6.QtDBus', 'PyQt6.QtQuick3D',
              'PyQt6.QtQuickWidgets', 'PyQt6.QtPrintSupport',
              'PyQt6.QtPositioning', 'PyQt6.QtSql',
              'PyQt6.QtOpenGLWidgets', 'PyQt6.QtOpenGL'],
    noarchive=False,
    optimize=0,
)

# Strip out unnecessary DLLs from the bundle
UNNEEDED_DLLS = {
    'opengl32sw.dll',        # Software OpenGL renderer — 20 MB
    'd3dcompiler_47.dll',    # Direct3D compiler — unused
    'qt6pdf.dll',            # PDF module — unused
    'qt6network.dll',        # Network module — unused
}
a.binaries = [b for b in a.binaries if b[0].split('\\')[-1].split('/')[-1].lower() not in UNNEEDED_DLLS]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TodoList',
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
)
