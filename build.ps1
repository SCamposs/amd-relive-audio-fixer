$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --windowed --name FixerAudioAMD --icon assets/app-icon.ico --add-data 'assets:assets' --add-data 'fonts:fonts' corretor_audio.py
if ($LASTEXITCODE) { throw 'PyInstaller failed' }
$compiler = Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
& $compiler installer.iss
if ($LASTEXITCODE) { throw 'Installer compilation failed' }
