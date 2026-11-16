"""Windows WebView2 shell and narrow frontend bridge. Media engine stays independent."""
import ctypes
import json
import os
import sys
import threading
import webbrowser
from pathlib import Path
import webview
from . import VERSION, engine, services

class Api:
    def __init__(self):
        self._window = None
        self._lock = threading.RLock()
        self._cancelled = threading.Event()
        self._settings = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'FixerAudioAMD' / 'settings.json'
        try:
            output = json.loads(self._settings.read_text(encoding='utf-8')).get('output')
        except (OSError, ValueError):
            output = None
        self._data = {'version': VERSION, 'files': [], 'busy': False, 'status': 'Pronto para começar',
                     'output': output or str(Path.home() / 'Downloads'), 'log': [], 'update': False,
                     'ffmpeg': bool(engine.tool('ffmpeg')), 'maximized': False}
        self._asset = None

    def state(self):
        with self._lock:
            return json.loads(json.dumps(self._data))

    def add_files(self, paths):
        with self._lock:
            if self._data['busy']:
                return
            for value in paths:
                path = Path(value).resolve()
                if path.is_file() and str(path) not in [f['path'] for f in self._data['files']]:
                    self._data['files'].append({'path': str(path), 'name': path.name,
                        'size': path.stat().st_size, 'status': 'Na fila'})

    def pick_files(self):
        if self._data['busy']:
            return
        paths = self._window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=True,
            file_types=('Mídia (*.mp4;*.mkv;*.mov;*.avi;*.webm;*.mp3;*.flac;*.wav;*.m4a;*.aac;*.ogg;*.opus)', 'Todos os arquivos (*.*)'))
        if paths:
            self.add_files(paths)

    def remove_files(self, paths):
        with self._lock:
            if not self._data['busy']:
                self._data['files'] = [f for f in self._data['files'] if f['path'] not in paths]

    def pick_output(self):
        if self._data['busy']:
            return
        paths = self._window.create_file_dialog(webview.FileDialog.FOLDER, directory=self._data['output'])
        if paths:
            with self._lock:
                self._data['output'] = paths[0]
                self._settings.parent.mkdir(parents=True, exist_ok=True)
                self._settings.write_text(json.dumps({'output': paths[0]}), encoding='utf-8')

    def open_output(self):
        os.startfile(self._data['output'])

    def start_batch(self, mode, audio_format, overwrite=False):
        with self._lock:
            if self._data['busy']:
                return
            if mode not in range(4) or audio_format not in ('FLAC', 'WAV', 'MP3'):
                raise ValueError('Operação inválida')
            if not self._data['files']:
                raise ValueError('Adicione pelo menos um arquivo.')
            if not engine.tool('ffmpeg'):
                raise ValueError('Instale o FFmpeg pelo menu Ferramentas.')
            if not Path(self._data['output']).is_dir():
                raise ValueError('Escolha uma pasta de saída existente.')
            files = [f['path'] for f in self._data['files']]
            for item in self._data['files']:
                item['status'] = 'Na fila'
            self._data.update(busy=True, status='Preparando fila…', log=[])
            self._cancelled.clear()
        threading.Thread(target=self._batch, args=(files, mode, audio_format, overwrite), daemon=True).start()

    def _batch(self, files, mode, audio_format, overwrite):
        good = bad = 0
        try:
            for index, value in enumerate(files):
                if self._cancelled.is_set():
                    break
                def progress(time):
                    with self._lock:
                        self._data['files'][index]['status'] = 'Processando'
                        self._data['status'] = f'Arquivo {index+1} de {len(files)} · {time}'
                try:
                    progress('00:00:00')
                    target = engine.execute(Path(value), Path(self._data['output']), mode,
                        audio_format, bool(overwrite and mode == 1), progress, self._cancelled.is_set)
                    with self._lock:
                        self._data['files'][index]['status'] = 'Concluído'
                        self._data['log'].append(f'✓ {Path(value).name}\n{target}')
                    good += 1
                except InterruptedError:
                    with self._lock:
                        self._data['files'][index]['status'] = 'Cancelado'
                    break
                except Exception as error:
                    bad += 1
                    with self._lock:
                        self._data['files'][index]['status'] = 'Falhou'
                        self._data['log'].append(f'{Path(value).name}: {error}')
        finally:
            with self._lock:
                self._data['busy'] = False
                self._data['status'] = f'{good} concluído(s) · {bad} falha(s)' + (' · Cancelado' if self._cancelled.is_set() else '')

    def cancel(self):
        self._cancelled.set()

    def window_action(self, action):
        if action == 'minimize':
            self._window.minimize()
        elif action == 'maximize':
            self._window.restore() if self._data['maximized'] else self._window.maximize()
            self._data['maximized'] = not self._data['maximized']
        elif action == 'close':
            self._window.destroy()

    def closing(self, *_):
        if self._data['busy']:
            with self._lock:
                self._data['status'] = 'Cancele ou aguarde a tarefa antes de fechar.'
            return False

    def _task(self, function, callback):
        with self._lock:
            if self._data['busy']:
                return
            self._data['busy'] = True
        def work():
            try:
                result = function()
                callback(result)
            except Exception as error:
                with self._lock:
                    self._data['status'] = str(error)
                    self._data['log'].append(str(error))
            finally:
                with self._lock:
                    self._data['busy'] = False
        threading.Thread(target=work, daemon=True).start()

    def install_ffmpeg(self):
        self._data['status'] = 'Baixando e verificando FFmpeg…'
        def ready(result):
            with self._lock:
                self._data.update(status=result, ffmpeg=True)
        self._task(services.install_ffmpeg, ready)

    def check_updates(self, manual=False):
        def work():
            try:
                asset = services.latest()
                with self._lock:
                    self._asset = asset
                    self._data['update'] = bool(asset)
                    if manual:
                        self._data['status'] = 'Nova versão disponível' if asset else 'Você está na versão mais recente.'
            except Exception:
                if manual:
                    self._data['status'] = 'Não foi possível consultar atualizações.'
        threading.Thread(target=work, daemon=True).start()

    def install_update(self):
        if self._asset:
            self._data['status'] = 'Baixando e verificando atualização…'
            def ready(path):
                os.startfile(path)
                with self._lock:
                    self._data['busy'] = False
                self._window.destroy()
            self._task(lambda: services.download_update(self._asset), ready)

    def project(self):
        webbrowser.open(services.REPOSITORY)

def main():
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('SCamposs.FixerAudioAMD')
    api = Api()
    api._window = webview.create_window('Fixer Audio', str(root / 'frontend/dist/index.html'),
        js_api=api, width=1120, height=850, min_size=(860, 700), frameless=True,
        easy_drag=False, background_color='#09090b', text_select=False)
    api._window.events.closing += api.closing
    def loaded(*_):
        def dropped(event):
            paths = [f.get('pywebviewFullPath') for f in event.get('dataTransfer', {}).get('files', [])]
            api.add_files([p for p in paths if p])
        api._window.dom.document.events.drop += dropped
        api.check_updates()
    api._window.events.loaded += loaded
    webview.start(gui='edgechromium', icon=str(root / 'assets/app-icon.ico'), http_server=True)
