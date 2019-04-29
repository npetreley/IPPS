# -*- mode: python -*-

block_cipher = None


a = Analysis(['D:\\Git\\IPPS\\venv\\Scripts\\IPPS\\src\\main\\python\\main.py'],
             pathex=['D:\\Git\\IPPS\\venv\\Scripts\\IPPS\\target\\PyInstaller'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=['d:\\git\\ipps\\venv\\lib\\site-packages\\fbs\\freeze\\hooks'],
             runtime_hooks=['C:\\Users\\npetrele\\AppData\\Local\\Temp\\tmp5hja4kwg\\fbs_pyinstaller_hook.py'],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='TestIPPS',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False , icon='D:\\Git\\IPPS\\venv\\Scripts\\IPPS\\src\\main\\icons\\Icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='TestIPPS')
