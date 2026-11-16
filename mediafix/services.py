"""Verified dependency downloads and GitHub releases."""
import hashlib
import json
import os
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from . import VERSION

REPOSITORY = "https://github.com/SCamposs/amd-relive-audio-fixer"
def request(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": f"FixerAudioAMD/{VERSION}"}), timeout=30)

def latest():
    with request("https://api.github.com/repos/SCamposs/amd-relive-audio-fixer/releases/latest") as response:
        data = json.load(response)
    key = lambda value: tuple(int(p) for p in value.lstrip("v").split("."))
    if key(data["tag_name"]) <= key(VERSION):
        return None
    return next((a for a in data["assets"] if a["name"] == "FixerAudioAMD-Setup.exe"), None)

def download_update(asset):
    digest = asset.get("digest", "") or ""
    if not digest.startswith("sha256:"):
        raise RuntimeError("A release não contém SHA-256 verificável.")
    directory = Path(tempfile.mkdtemp(prefix="fixeraudio-update-"))
    target = directory / "FixerAudioAMD-Setup.exe"
    try:
        with request(asset["browser_download_url"]) as response, target.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest.split(":", 1)[1]:
            raise RuntimeError("SHA-256 da atualização inválido.")
        return str(target)
    except Exception:
        target.unlink(missing_ok=True)
        directory.rmdir()
        raise

def install_ffmpeg():
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    directory = Path(os.environ["LOCALAPPDATA"]) / "FixerAudioAMD" / "bin"
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ffmpeg-") as temporary:
        archive = Path(temporary) / "ffmpeg.zip"
        with request(url) as response, archive.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        with request(url + ".sha256") as response:
            expected = response.read().decode().split()[0]
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected.lower():
            raise RuntimeError("SHA-256 do FFmpeg inválido.")
        with zipfile.ZipFile(archive) as package:
            for executable in ("ffmpeg.exe", "ffprobe.exe"):
                member = next(n for n in package.namelist() if n.endswith("/bin/" + executable))
                staging = directory / (executable + ".tmp")
                staging.write_bytes(package.read(member))
                os.replace(staging, directory / executable)
    return "FFmpeg e FFprobe instalados."
