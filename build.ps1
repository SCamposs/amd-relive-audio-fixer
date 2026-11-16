$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$originalPath = $env:PATH
try {
    # Dependency discovery must not use DLLs from unrelated tools on the host PATH.
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot;$PSScriptRoot\.venv\Scripts"
    & .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean packaging/windows.spec
    if ($LASTEXITCODE) { throw 'PyInstaller failed' }
    & .\.venv\Scripts\python.exe packaging/verify_bundle.py
    if ($LASTEXITCODE) { throw 'Bundle verification failed' }
} finally {
    $env:PATH = $originalPath
}
$compiler = Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
& $compiler installer.iss
if ($LASTEXITCODE) { throw 'Installer compilation failed' }
