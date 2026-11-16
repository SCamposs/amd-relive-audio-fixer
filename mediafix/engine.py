"""Media operations, independent of the graphical interface."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

MODES = ["Corrigir áudio 7.1 → estéreo", "Limpar metadados", "Extrair áudio", "MP4 compatível (H.264)"]

def tool(name):
    private = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "FixerAudioAMD" / "bin" / f"{name}.exe"
    return str(private) if private.is_file() else shutil.which(name)

def options():
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}

def arguments(source, output, mode, audio_format="FLAC"):
    base = ["-hide_banner", "-nostdin", "-y", "-i", str(source)]
    if mode == 0:
        args = ["-map", "0:V?", "-map", "0:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ac", "2"]
    elif mode == 1:
        args = ["-map", "0:V?", "-map", "0:a?", "-map", "0:s?", "-map_metadata", "-1", "-map_metadata:s", "-1", "-map_chapters", "-1", "-c", "copy", "-fflags", "+bitexact"]
        if source.suffix.lower() == ".mp3":
            args += ["-id3v2_version", "0"]
    elif mode == 2:
        codec = {"FLAC": ["flac"], "WAV": ["pcm_f32le"], "MP3": ["libmp3lame", "-b:a", "320k"]}[audio_format]
        args = ["-map", "0:a:0", "-vn", "-c:a", *codec]
    else:
        args = ["-map", "0:V:0", "-map", "0:a?", "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ac", "2", "-movflags", "+faststart"]
    return base + args + ["-progress", "pipe:1", "-nostats", str(output)]

def output_path(source, directory, mode, audio_format):
    suffix = source.suffix if mode == 1 else ("." + audio_format.lower() if mode == 2 else ".mp4")
    stem = source.stem + ["_stereo", "_limpo", "_audio", "_compativel"][mode]
    target = directory / (stem + suffix)
    counter = 2
    while target.exists():
        target = directory / f"{stem}_{counter}{suffix}"
        counter += 1
    return target

def execute(source, directory, mode, audio_format, overwrite, progress, cancelled):
    ffmpeg = tool("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg ausente. Instale-o pelo menu Ferramentas.")
    target = source if mode == 1 and overwrite else output_path(source, directory, mode, audio_format)
    handle, name = tempfile.mkstemp(prefix=".mediafix-", suffix=target.suffix, dir=target.parent)
    os.close(handle)
    temp = Path(name)
    try:
        with tempfile.TemporaryFile() as errors:
            process = subprocess.Popen([ffmpeg, *arguments(source, temp, mode, audio_format)], stdout=subprocess.PIPE, stderr=errors, text=True, **options())
            import threading
            done = threading.Event()
            def watch():
                while not done.wait(0.1):
                    if cancelled():
                        process.terminate()
                        return
            watcher = threading.Thread(target=watch, daemon=True)
            watcher.start()
            try:
                for line in process.stdout:
                    if line.startswith("out_time="):
                        progress(line.strip().split("=", 1)[1])
                process.wait()
            finally:
                done.set()
                process.stdout.close()
            if cancelled():
                raise InterruptedError("Cancelado")
            if process.returncode:
                errors.seek(0)
                raise RuntimeError(errors.read().decode("utf-8", errors="replace")[-2500:])
        if target == source:
            shutil.copystat(source, temp)
        os.replace(temp, target)
        return target
    finally:
        temp.unlink(missing_ok=True)
