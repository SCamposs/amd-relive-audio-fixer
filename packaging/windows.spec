from pathlib import Path

root = Path(SPECPATH).parent
a = Analysis([str(root / 'corretor_audio.py')], pathex=[str(root)],
             binaries=[], datas=[(str(root / 'assets'), 'assets'), (str(root / 'frontend/dist'), 'frontend/dist')],
             hiddenimports=['webview.platforms.edgechromium', 'webview.platforms.winforms'], hookspath=[], runtime_hooks=[],
             excludes=['PySide6', 'PyQt6', 'PyQt5', 'tkinter', 'webview.platforms.qt'], noarchive=False)
# Qt 6.12 uses the Windows ICU ABI (unversioned exports). A third-party ICU
# found on the build host PATH is not interchangeable with the system library.
a.binaries = [entry for entry in a.binaries
              if Path(entry[0]).name.lower() not in {'icuuc.dll', 'icudt78.dll'}]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='FixerAudioAMD',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, icon=str(root / 'assets/app-icon.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='FixerAudioAMD')
