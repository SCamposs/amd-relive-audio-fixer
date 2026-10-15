from __future__ import annotations

import ctypes
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


APP_TITLE = "Fixer de Áudio AMD ReLive"
WINDOW_WIDTH = 780
WINDOW_HEIGHT = 620
FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
FFMPEG_CHECKSUM_URL = f"{FFMPEG_DOWNLOAD_URL}.sha256"

COLORS = {
    "bg": "#101014",
    "titlebar": "#0B0B0E",
    "surface": "#1D1D23",
    "surface_hover": "#25252D",
    "line": "#303038",
    "text": "#F2F0EA",
    "muted": "#AAA8B2",
    "subtle": "#777681",
    "button": "#E9E5DA",
    "button_hover": "#FFFFFF",
    "button_text": "#111115",
    "primary": "#F3A812",
    "primary_hover": "#FFC02E",
    "success": "#00DD80",
    "cyan": "#00CBEA",
    "lime": "#B4D82B",
    "orange": "#FF9C16",
    "red": "#FF4D24",
}

FONT_LOGO = "Century Gothic"
FONT_UI = "Barlow"
FONT_DISPLAY = "Barlow Semi Condensed"
FONT_MONO = "JetBrains Mono"


def resource_path(relative_path: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative_path


def load_private_fonts() -> None:
    if os.name != "nt":
        return
    add_font = ctypes.windll.gdi32.AddFontResourceExW
    for font_name in (
        "Barlow-Regular.ttf",
        "Barlow-SemiBold.ttf",
        "BarlowSemiCondensed-Bold.ttf",
        "JetBrainsMono-Regular.ttf",
    ):
        font_path = resource_path(f"fonts/{font_name}")
        if font_path.is_file():
            add_font(str(font_path), 0x10, 0)


class ActionButton(tk.Canvas):
    def __init__(
        self,
        master: tk.Misc,
        text: str,
        command,
        *,
        width: int,
        height: int,
        bg: str,
        hover_bg: str,
        fg: str,
        font: tuple,
        radius: int = 9,
    ) -> None:
        super().__init__(
            master,
            width=width,
            height=height,
            bg=COLORS["bg"],
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            takefocus=1,
        )
        self._text = text
        self._command = command
        self._normal_bg = bg
        self._hover_bg = hover_bg
        self._fg = fg
        self._font = font
        self._radius = radius
        self._enabled = True
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", lambda _event: self._draw(self._hover_bg))
        self.bind("<Leave>", lambda _event: self._draw())
        self.bind("<Button-1>", self._invoke)
        self.bind("<Return>", self._invoke)
        self.bind("<space>", self._invoke)
        self.bind("<FocusIn>", lambda _event: self._draw(focused=True))
        self.bind("<FocusOut>", lambda _event: self._draw())
        self._draw()

    @staticmethod
    def _rounded_rect(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)

    def _draw(self, fill: str | None = None, focused: bool = False) -> None:
        self.delete("all")
        width = max(self.winfo_width(), int(self["width"]))
        height = max(self.winfo_height(), int(self["height"]))
        color = fill or self._normal_bg
        if not self._enabled:
            color = COLORS["surface_hover"]
        outline = COLORS["success"] if focused and self._enabled else color
        self._rounded_rect(
            self, 1, 1, width - 1, height - 1, self._radius,
            fill=color, outline=outline, width=2 if focused else 1,
        )
        self.create_text(
            width / 2,
            height / 2,
            text=self._text,
            fill=self._fg if self._enabled else COLORS["subtle"],
            font=self._font,
        )

    def _invoke(self, _event=None) -> None:
        if self._enabled:
            self._command()

    def configure_state(self, enabled: bool, text: str | None = None) -> None:
        self._enabled = enabled
        if text is not None:
            self._text = text
        self.configure(cursor="hand2" if enabled else "arrow")
        self._draw()


class FixerAudioApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.configure(bg=COLORS["bg"])
        self.root.overrideredirect(True)
        self.root.resizable(False, False)
        self._center_window()

        self.origem = tk.StringVar()
        self.destino = tk.StringVar()
        self.status = tk.StringVar(value="Aguardando um clipe MP4")
        self.percentual = tk.StringVar(value="—")
        self._drag_x = 0
        self._drag_y = 0
        self._conversion_active = False
        self._download_active = False
        self._progress_step = 0
        self._progress_job: str | None = None
        self._ffmpeg_path = self._locate_ffmpeg()

        self._build_ui()
        self.root.after(50, self._apply_windows_style)
        self.root.after(450, self._check_ffmpeg_on_startup)

    def _center_window(self) -> None:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = max((screen_w - WINDOW_WIDTH) // 2, 0)
        y = max((screen_h - WINDOW_HEIGHT) // 2, 0)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    def _native_hwnd(self) -> int | None:
        if os.name != "nt":
            return None
        self.root.update_idletasks()
        return ctypes.windll.user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()

    def _apply_windows_style(self) -> None:
        hwnd = self._native_hwnd()
        if not hwnd:
            return
        try:
            gwl_exstyle = -20
            ws_ex_toolwindow = 0x00000080
            ws_ex_appwindow = 0x00040000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, gwl_exstyle)
            style = (style & ~ws_ex_toolwindow) | ws_ex_appwindow
            ctypes.windll.user32.SetWindowLongW(hwnd, gwl_exstyle, style)
            corner = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(corner), ctypes.sizeof(corner)
            )
        except (AttributeError, OSError):
            pass

    def _build_ui(self) -> None:
        shell = tk.Frame(self.root, bg=COLORS["bg"], highlightthickness=1, highlightbackground="#050506")
        shell.pack(fill="both", expand=True)
        self._build_titlebar(shell)

        content = tk.Frame(shell, bg=COLORS["bg"], padx=36, pady=30)
        content.pack(fill="both", expand=True)

        tk.Label(
            content,
            text="CONVERSÃO DE ÁUDIO",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=(FONT_DISPLAY, 25, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            content,
            text="Repare faixas 7.1 sem som capturadas pelo AMD ReLive.",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=(FONT_UI, 11),
            anchor="w",
        ).pack(fill="x", pady=(2, 18))
        tk.Frame(content, bg=COLORS["line"], height=1).pack(fill="x", pady=(0, 22))

        self._build_file_field(
            content,
            "Vídeo original",
            "áudio 7.1 sem som",
            self.origem,
            "PROCURAR…",
            self.selecionar_origem,
            "origin",
        )
        self._build_file_field(
            content,
            "Salvar vídeo corrigido em",
            None,
            self.destino,
            "ALTERAR…",
            self.selecionar_destino,
            "destination",
        )

        self.convert_button = ActionButton(
            content,
            "CORRIGIR ÁUDIO PARA ESTÉREO",
            self.iniciar_conversao,
            width=700,
            height=64,
            bg=COLORS["primary"],
            hover_bg=COLORS["primary_hover"],
            fg="#111115",
            font=(FONT_UI, 13, "bold"),
            radius=10,
        )
        self.convert_button.pack(fill="x", pady=(6, 25))

        self.progress = tk.Canvas(
            content, height=8, bg=COLORS["surface"], bd=0, highlightthickness=0
        )
        self.progress.pack(fill="x")
        self.progress.bind("<Configure>", lambda _event: self._draw_progress(0))

        status_row = tk.Frame(content, bg=COLORS["bg"])
        status_row.pack(fill="x", pady=(13, 0))
        self.status_icon = tk.Label(
            status_row,
            text="◆",
            bg=COLORS["bg"],
            fg=COLORS["subtle"],
            font=(FONT_UI, 10, "bold"),
        )
        self.status_icon.pack(side="left")
        self.status_label = tk.Label(
            status_row,
            textvariable=self.status,
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=(FONT_UI, 10, "bold"),
        )
        self.status_label.pack(side="left", padx=(10, 0))
        tk.Label(
            status_row,
            textvariable=self.percentual,
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=(FONT_MONO, 9),
        ).pack(side="right")

        footer = tk.Frame(shell, bg=COLORS["titlebar"], height=52)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        tk.Label(
            footer,
            text="STEREO REMUX  •  AAC 2.0",
            bg=COLORS["titlebar"],
            fg=COLORS["subtle"],
            font=(FONT_MONO, 9),
        ).pack(side="left", padx=30)
        tk.Label(
            footer,
            text="AMD RELIVE UTILITY",
            bg=COLORS["titlebar"],
            fg=COLORS["subtle"],
            font=(FONT_MONO, 9),
        ).pack(side="right", padx=30)

    def _build_titlebar(self, shell: tk.Frame) -> None:
        titlebar = tk.Frame(shell, bg=COLORS["titlebar"], height=64)
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)
        titlebar.bind("<ButtonPress-1>", self._start_drag)
        titlebar.bind("<B1-Motion>", self._drag_window)

        logo = tk.Canvas(titlebar, width=64, height=34, bg=COLORS["titlebar"], bd=0, highlightthickness=0)
        logo.pack(side="left", padx=(18, 8))
        slash_colors = (COLORS["cyan"], COLORS["success"], COLORS["lime"], COLORS["orange"], COLORS["red"])
        for index, color in enumerate(slash_colors):
            x = 3 + index * 11
            logo.create_polygon(x + 7, 3, x + 15, 3, x + 7, 31, x - 1, 31, fill=color, outline="")

        title = tk.Label(
            titlebar,
            text=APP_TITLE,
            bg=COLORS["titlebar"],
            fg=COLORS["text"],
            font=(FONT_LOGO, 10, "bold"),
        )
        title.pack(side="left")
        title.bind("<ButtonPress-1>", self._start_drag)
        title.bind("<B1-Motion>", self._drag_window)

        close = self._title_button(titlebar, "×", self._request_close, hover="#D33B3B")
        close.pack(side="right", fill="y")
        minimize = self._title_button(titlebar, "−", self._minimize)
        minimize.pack(side="right", fill="y")

    def _title_button(self, master: tk.Misc, text: str, command, hover: str | None = None) -> tk.Label:
        label = tk.Label(
            master,
            text=text,
            width=5,
            bg=COLORS["titlebar"],
            fg=COLORS["muted"],
            font=(FONT_UI, 14),
            cursor="hand2",
        )
        hover_color = hover or COLORS["surface_hover"]
        label.bind("<Enter>", lambda _event: label.configure(bg=hover_color, fg=COLORS["text"]))
        label.bind("<Leave>", lambda _event: label.configure(bg=COLORS["titlebar"], fg=COLORS["muted"]))
        label.bind("<Button-1>", lambda _event: command())
        return label

    def _build_file_field(
        self,
        master: tk.Misc,
        label: str,
        detail: str | None,
        variable: tk.StringVar,
        button_text: str,
        command,
        key: str,
    ) -> None:
        label_row = tk.Frame(master, bg=COLORS["bg"])
        label_row.pack(fill="x", pady=(0, 8))
        tk.Label(
            label_row,
            text=label,
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=(FONT_UI, 10, "bold"),
        ).pack(side="left")
        if detail:
            tk.Label(
                label_row,
                text=f" ({detail})",
                bg=COLORS["bg"],
                fg=COLORS["muted"],
                font=(FONT_UI, 10),
            ).pack(side="left")

        row = tk.Frame(master, bg=COLORS["bg"])
        row.pack(fill="x", pady=(0, 24))
        field = tk.Frame(row, bg=COLORS["line"], padx=1, pady=1)
        field.pack(side="left", fill="x", expand=True)
        entry = tk.Entry(
            field,
            textvariable=variable,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            insertbackground=COLORS["primary"],
            disabledbackground=COLORS["surface"],
            disabledforeground=COLORS["subtle"],
            relief="flat",
            bd=0,
            font=(FONT_MONO, 10),
        )
        entry.pack(fill="x", ipady=15, padx=14)
        button = ActionButton(
            row,
            button_text,
            command,
            width=145,
            height=52,
            bg=COLORS["button"],
            hover_bg=COLORS["button_hover"],
            fg=COLORS["button_text"],
            font=(FONT_UI, 9, "bold"),
            radius=9,
        )
        button.pack(side="right", padx=(12, 0))

        if key == "origin":
            self.origin_entry = entry
            self.origin_button = button
        else:
            self.destination_entry = entry
            self.destination_button = button

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_window(self, event: tk.Event) -> None:
        self.root.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    def _minimize(self) -> None:
        hwnd = self._native_hwnd()
        if hwnd and os.name == "nt":
            ctypes.windll.user32.ShowWindow(hwnd, 6)
        else:
            self.root.iconify()

    def _request_close(self) -> None:
        if (self._conversion_active or self._download_active) and not messagebox.askyesno(
            APP_TITLE,
            "Uma operação ainda está em andamento. Deseja fechar mesmo assim?",
            parent=self.root,
        ):
            return
        self.root.destroy()

    @staticmethod
    def _downloads_folder() -> Path:
        downloads = Path.home() / "Downloads"
        return downloads if downloads.is_dir() else Path.home()

    def selecionar_origem(self) -> None:
        file_path = filedialog.askopenfilename(
            parent=self.root,
            title="Selecione o clipe gravado pela AMD ReLive",
            initialdir=self._downloads_folder(),
            filetypes=(("Vídeo MP4", "*.mp4"), ("Todos os arquivos", "*.*")),
        )
        if not file_path:
            return
        source = Path(file_path)
        destination = self._downloads_folder() / f"{source.stem}_corrigido.mp4"
        self.origem.set(str(source))
        self.destino.set(str(destination))
        self._set_status("ready", "Pronto para converter", "0%")

    def selecionar_destino(self) -> None:
        current = Path(self.destino.get()) if self.destino.get() else None
        file_path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Salvar vídeo corrigido",
            initialdir=current.parent if current else self._downloads_folder(),
            initialfile=current.name if current else "video_corrigido.mp4",
            defaultextension=".mp4",
            filetypes=(("Vídeo MP4", "*.mp4"),),
        )
        if file_path:
            self.destino.set(file_path)

    @staticmethod
    def _private_ffmpeg_path() -> Path:
        local_app_data = os.environ.get("LOCALAPPDATA")
        base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
        return base / "FixerAudioAMD" / "bin" / "ffmpeg.exe"

    @classmethod
    def _locate_ffmpeg(cls) -> str | None:
        executable = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        app_dir = (
            Path(sys.executable).resolve().parent
            if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parent
        )
        local = app_dir / executable
        if local.is_file():
            return str(local)
        private = cls._private_ffmpeg_path()
        if private.is_file():
            return str(private)
        return shutil.which(executable)

    def _check_ffmpeg_on_startup(self) -> None:
        if not self._ffmpeg_path:
            self._offer_ffmpeg_download()

    def _offer_ffmpeg_download(self) -> None:
        if self._download_active:
            return
        download = messagebox.askyesno(
            "FFmpeg necessário",
            "O FFmpeg é necessário para corrigir o áudio e ainda não está disponível.\n\n"
            "Deseja baixar e configurar automaticamente agora? O download tem aproximadamente 110 MB.",
            parent=self.root,
        )
        if download:
            self._start_ffmpeg_download()
        else:
            self._set_status("error", "FFmpeg necessário para converter", "AUSENTE")

    def _start_ffmpeg_download(self) -> None:
        self._download_active = True
        self._set_controls_enabled(False)
        self.convert_button.configure_state(False, "BAIXANDO FFMPEG…")
        self._set_status("working", "Preparando download do FFmpeg", "0%")
        self._draw_progress(0)
        threading.Thread(target=self._download_ffmpeg, daemon=True).start()

    def _download_ffmpeg(self) -> None:
        install_path = self._private_ffmpeg_path()
        install_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_dir = Path(tempfile.mkdtemp(prefix="download-", dir=install_path.parent.parent))
        archive_path = temporary_dir / "ffmpeg.zip"
        extracted_path = temporary_dir / "ffmpeg.exe"

        try:
            request = urllib.request.Request(
                FFMPEG_DOWNLOAD_URL,
                headers={"User-Agent": "FixerAudioAMD/1.0"},
            )
            with urllib.request.urlopen(request, timeout=60) as response, archive_path.open("wb") as archive:
                total = int(response.headers.get("Content-Length", "0"))
                downloaded = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    archive.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        fraction = min(downloaded / total, 0.99)
                        self.root.after(0, self._update_download_progress, fraction)

            checksum_request = urllib.request.Request(
                FFMPEG_CHECKSUM_URL,
                headers={"User-Agent": "FixerAudioAMD/1.0"},
            )
            with urllib.request.urlopen(checksum_request, timeout=30) as response:
                expected_checksum = response.read().decode("ascii").strip().split()[0].lower()
            digest = hashlib.sha256()
            with archive_path.open("rb") as archive:
                for chunk in iter(lambda: archive.read(1024 * 1024), b""):
                    digest.update(chunk)
            actual_checksum = digest.hexdigest().lower()
            if actual_checksum != expected_checksum:
                raise RuntimeError("A verificação de segurança do download falhou.")

            with zipfile.ZipFile(archive_path) as package:
                member = next(
                    (name for name in package.namelist() if name.lower().endswith("/bin/ffmpeg.exe")),
                    None,
                )
                if member is None:
                    raise RuntimeError("O pacote baixado não contém ffmpeg.exe.")
                with package.open(member) as source, extracted_path.open("wb") as destination:
                    shutil.copyfileobj(source, destination)

            os.replace(extracted_path, install_path)
            self.root.after(0, self._ffmpeg_download_complete, str(install_path))
        except Exception as error:
            self.root.after(0, self._ffmpeg_download_failed, str(error))
        finally:
            shutil.rmtree(temporary_dir, ignore_errors=True)

    def _update_download_progress(self, fraction: float) -> None:
        self._draw_progress(fraction)
        percent = max(1, min(round(fraction * 100), 99))
        self._set_status("working", "Baixando FFmpeg", f"{percent}%")

    def _ffmpeg_download_complete(self, ffmpeg_path: str) -> None:
        self._ffmpeg_path = ffmpeg_path
        self._download_active = False
        self._set_controls_enabled(True)
        self.convert_button.configure_state(True, "CORRIGIR ÁUDIO PARA ESTÉREO")
        self._draw_progress(1)
        self._set_status("success", "FFmpeg instalado. Pronto para converter", "100%")

    def _ffmpeg_download_failed(self, error: str) -> None:
        self._download_active = False
        self._set_controls_enabled(True)
        self.convert_button.configure_state(True, "CORRIGIR ÁUDIO PARA ESTÉREO")
        self._draw_progress(0)
        self._set_status("error", "Não foi possível instalar o FFmpeg", "ERRO")
        messagebox.showerror(
            "Falha no download",
            f"Não foi possível baixar ou validar o FFmpeg.\n\n{error}",
            parent=self.root,
        )

    @staticmethod
    def _subprocess_options() -> dict[str, object]:
        if os.name != "nt":
            return {}
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return {"startupinfo": startupinfo, "creationflags": subprocess.CREATE_NO_WINDOW}

    def iniciar_conversao(self) -> None:
        source_text = self.origem.get().strip()
        destination_text = self.destino.get().strip()
        source = Path(source_text)
        destination = Path(destination_text)

        if not source_text or not source.is_file() or source.suffix.lower() != ".mp4":
            messagebox.showwarning(APP_TITLE, "Selecione um arquivo MP4 de entrada válido.", parent=self.root)
            return
        if not destination_text or destination.suffix.lower() != ".mp4":
            messagebox.showwarning(APP_TITLE, "Informe um arquivo MP4 de saída válido.", parent=self.root)
            return
        if source.resolve() == destination.resolve():
            messagebox.showwarning(APP_TITLE, "A origem e o destino não podem ser o mesmo arquivo.", parent=self.root)
            return
        if destination.exists() and not messagebox.askyesno(
            APP_TITLE, "O arquivo de destino já existe. Deseja substituí-lo?", parent=self.root
        ):
            return

        ffmpeg = self._ffmpeg_path or self._locate_ffmpeg()
        if not ffmpeg:
            self._offer_ffmpeg_download()
            return

        destination.parent.mkdir(parents=True, exist_ok=True)
        self._set_converting(True)
        threading.Thread(
            target=self._convert_in_background,
            args=(ffmpeg, source, destination),
            daemon=True,
        ).start()

    def _convert_in_background(self, ffmpeg: str, source: Path, destination: Path) -> None:
        command = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-i", str(source), "-c:v", "copy", "-c:a", "aac", "-ac", "2",
            str(destination),
        ]
        try:
            result = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                **self._subprocess_options(),
            )
            if result.returncode == 0:
                self.root.after(0, self._conversion_complete, destination)
            else:
                error = result.stderr.strip() or f"FFmpeg encerrou com o código {result.returncode}."
                self.root.after(0, self._conversion_failed, error)
        except OSError as error:
            self.root.after(0, self._conversion_failed, str(error))

    def _set_converting(self, converting: bool) -> None:
        self._conversion_active = converting
        self._set_controls_enabled(not converting)
        self.convert_button.configure_state(
            not converting,
            "CONVERTENDO ÁUDIO…" if converting else "CORRIGIR ÁUDIO PARA ESTÉREO",
        )
        if converting:
            self._set_status("working", "Convertendo áudio 7.1 para estéreo", "EM CURSO")
            self._animate_progress()
        else:
            self._stop_progress_animation()

    def _set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.origin_entry.configure(state=state)
        self.destination_entry.configure(state=state)
        self.origin_button.configure_state(enabled)
        self.destination_button.configure_state(enabled)

    def _draw_progress(self, fraction: float, offset: float = 0.0) -> None:
        self.progress.delete("all")
        width = max(self.progress.winfo_width(), 1)
        self.progress.create_rectangle(0, 0, width, 8, fill=COLORS["surface"], outline="")
        if fraction >= 1:
            self.progress.create_rectangle(0, 0, width, 8, fill=COLORS["success"], outline="")
        elif fraction > 0:
            segment = width * fraction
            start = (width + segment) * offset - segment
            self.progress.create_rectangle(start, 0, start + segment, 8, fill=COLORS["primary"], outline="")

    def _animate_progress(self) -> None:
        if not self._conversion_active:
            return
        self._progress_step = (self._progress_step + 1) % 100
        phase = self._progress_step / 99
        self._draw_progress(0.28, phase)
        self._progress_job = self.root.after(18, self._animate_progress)

    def _stop_progress_animation(self) -> None:
        if self._progress_job:
            self.root.after_cancel(self._progress_job)
            self._progress_job = None

    def _set_status(self, state: str, text: str, percent: str) -> None:
        state_style = {
            "idle": ("◆", COLORS["subtle"]),
            "ready": ("◆", COLORS["primary"]),
            "working": ("◆", COLORS["primary"]),
            "success": ("✓", COLORS["success"]),
            "error": ("!", COLORS["red"]),
        }
        icon, color = state_style[state]
        self.status_icon.configure(text=icon, fg=color)
        self.status_label.configure(fg=COLORS["text"] if state == "success" else COLORS["muted"])
        self.status.set(text)
        self.percentual.set(percent)

    def _conversion_complete(self, destination: Path) -> None:
        self._set_converting(False)
        self._draw_progress(1)
        self._set_status("success", "Conversão concluída com sucesso", "100%")
        messagebox.showinfo(APP_TITLE, f"Vídeo corrigido e salvo em:\n{destination}", parent=self.root)

    def _conversion_failed(self, error: str) -> None:
        self._set_converting(False)
        self._draw_progress(0)
        self._set_status("error", "A conversão falhou", "ERRO")
        summary = error if len(error) <= 1200 else f"{error[:1200]}\n\n[Mensagem resumida]"
        messagebox.showerror(APP_TITLE, f"O FFmpeg encontrou um erro:\n\n{summary}", parent=self.root)


def main() -> None:
    load_private_fonts()
    root = tk.Tk()
    FixerAudioApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
