# -*- mode: python ; coding: utf-8 -*-


block_cipher = None
crt_src = r'C:\Users\kaos\Documents\stream\Lib\site-packages\seleniumwire\ca.crt'
key_src = r'C:\Users\kaos\Documents\stream\Lib\site-packages\seleniumwire\ca.key'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        ('third_party/geckodriver.exe', '.'),
        ('C:/Program Files/VideoLAN/VLC/libvlc.dll', '.'),
        ('C:/Program Files/VideoLAN/VLC/libvlccore.dll', '.')
    ],
    datas=[
        ('third_party/FirefoxPortable', 'FirefoxPortable'),
        ('C:/Program Files/VideoLAN/VLC/plugins', 'plugins'),
        (crt_src, 'seleniumwire'),
        (key_src, 'seleniumwire'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='icon.ico'
)