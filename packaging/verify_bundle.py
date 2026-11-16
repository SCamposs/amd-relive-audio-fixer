"""Fail the release build if unrelated ICU libraries are bundled again."""
from pathlib import Path
import ctypes
import os

root = Path(__file__).resolve().parent.parent
bundle = root / 'dist/FixerAudioAMD/_internal'
assert (bundle / 'frontend/dist/index.html').is_file(), 'Frontend missing'
assert not list(bundle.rglob('Qt6Core.dll')), 'Obsolete Qt runtime bundled'
assert not list(bundle.rglob('icuuc.dll')), 'Foreign ICU bundled'
assert not list(bundle.rglob('icudt78.dll')), 'Foreign ICU data bundled'
if os.name == 'nt':
    system_icu = Path(os.environ['SystemRoot']) / 'System32/icuuc.dll'
    library = ctypes.WinDLL(str(system_icu))
    assert library.ucnv_open, 'Windows ICU ABI unavailable'
print('Bundle dependency checks passed')
