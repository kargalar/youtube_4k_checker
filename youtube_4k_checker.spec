# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['youtube_4k_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('client_secret.json', '.'),
        ('README_OAuth_Setup.md', '.'),
        ('oauth_setup_instructions.md', '.'),
    ],
    hiddenimports=[
        'googleapiclient.discovery',
        'google_auth_oauthlib.flow',
        'google.auth.transport.requests',
        'google.oauth2.service_account',
        'PIL._tkinter_finder',
        'requests',
        'pickle',
        'threading',
        'webbrowser',
        'io',
        'json',
        'os',
        're'
    ],
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
    name='YouTube_4K_Checker',
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
    icon=None,  # İsteğe bağlı: .ico dosyası ekleyebilirsiniz
)
