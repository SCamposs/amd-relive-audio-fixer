import os
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl, QSettings
from PySide6.QtGui import QIcon, QDesktopServices, QFontDatabase
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QFileDialog, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QMessageBox, QPlainTextEdit, QSplitter,
    QAbstractItemView, QStyle)
from . import VERSION, engine, services

STYLE = """
QWidget {background:#101014;color:#f2f0ea;font-family:'Barlow';font-size:14px;}
QMenuBar,QMenu {background:#19191f;} QMenu::item {padding:9px 24px;}
QMenu::item:selected,QMenuBar::item:selected {background:#34343e;}
QPushButton {background:#24242c;border:1px solid #41414c;border-radius:6px;padding:10px 16px;}
QPushButton:hover {background:#33333d;border-color:#8e8e9f;} QPushButton:focus {border-color:#f3a812;}
QPushButton:disabled {color:#777781;background:#1b1b21;}
QPushButton#primary {background:#f3a812;color:#111115;font-weight:600;border:0;}
QPushButton#primary:hover {background:#ffc02e;}
QLineEdit,QComboBox {background:#1d1d25;border:1px solid #41414c;border-radius:6px;padding:10px;min-height:20px;}
QLineEdit:focus,QComboBox:focus {border-color:#f3a812;}
QComboBox::drop-down {width:30px;border:0;} QComboBox QAbstractItemView {background:#24242c;selection-background-color:#454551;padding:6px;}
QLabel#title {font-size:28px;font-weight:650;} QLabel#muted {color:#b4b4c0;}
QLabel#brand {font-size:18px;font-weight:650;} QLabel#stripe {background:#00cbea;min-height:3px;max-height:3px;}
QTableWidget {background:#16161c;border:1px solid #30303a;border-radius:6px;gridline-color:#30303a;selection-background-color:#34343f;}
QHeaderView::section {background:#22222a;border:0;border-bottom:1px solid #41414c;padding:12px;color:#bcbcc8;}
QTableWidget::item {padding:10px;} QPlainTextEdit {background:#16161c;border:1px solid #30303a;border-radius:6px;font-family:Consolas;font-size:12px;}
QProgressBar {background:#262630;border:0;border-radius:3px;max-height:6px;}
QProgressBar::chunk {background:#f3a812;border-radius:3px;} QCheckBox {spacing:9px;padding:5px;}
QStatusBar {color:#b4b4c0;background:#19191f;} QSplitter::handle {background:#30303a;}
"""

class Task(QThread):
    result = Signal(object)
    error = Signal(str)
    def __init__(self, function, parent):
        super().__init__(parent)
        self.function = function
    def run(self):
        try:
            self.result.emit(self.function())
        except Exception as exc:
            self.error.emit(str(exc))

class Batch(QThread):
    changed = Signal(int, str)
    detail = Signal(str)
    completed = Signal(int, int)
    def __init__(self, files, directory, mode, audio_format, overwrite, parent):
        super().__init__(parent)
        self.files, self.directory, self.mode = files, directory, mode
        self.audio_format, self.overwrite = audio_format, overwrite
    def run(self):
        good = bad = 0
        for index, source in enumerate(self.files):
            if self.isInterruptionRequested():
                break
            self.changed.emit(index, "Processando…")
            try:
                target = engine.execute(source, self.directory, self.mode, self.audio_format,
                    self.overwrite, lambda time: self.changed.emit(index, f"Processando · {time}"), self.isInterruptionRequested)
                good += 1
                self.changed.emit(index, "Concluído")
                self.detail.emit(f"✓ {source.name}\n  {target}")
            except InterruptedError:
                self.changed.emit(index, "Cancelado")
                break
            except Exception as exc:
                bad += 1
                self.changed.emit(index, "Falhou")
                self.detail.emit(f"Falha em {source.name}:\n{exc}")
        self.completed.emit(good, bad)

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Fixer Audio · {VERSION}")
        root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
        self.setWindowIcon(QIcon(str(root / "assets/app-icon.ico")))
        self.resize(1080, 800)
        self.setMinimumSize(850, 690)
        self.setAcceptDrops(True)
        self.files, self.tasks = [], []
        self.batch = self.update_asset = None
        self.settings = QSettings("SCamposs", "FixerAudioAMD")
        self.build()
        QTimer.singleShot(1000, self.check_updates)

    def button(self, text, callback, icon=None):
        widget = QPushButton(text)
        widget.clicked.connect(callback)
        if icon:
            widget.setIcon(self.style().standardIcon(icon))
        return widget

    def label(self, text, role=None):
        widget = QLabel(text)
        if role:
            widget.setObjectName(role)
        return widget

    def build(self):
        menu = self.menuBar().addMenu("Arquivo")
        menu.addAction("Adicionar arquivos…", self.pick_files).setShortcut("Ctrl+O")
        menu.addAction("Abrir pasta de saída", self.open_output)
        menu.addSeparator()
        menu.addAction("Sair", self.close)
        tools = self.menuBar().addMenu("Ferramentas")
        tools.addAction("Instalar / atualizar FFmpeg", self.install_engine)
        tools.addAction("Verificar atualizações", lambda: self.check_updates(True))
        tools.addAction("Página do projeto", lambda: QDesktopServices.openUrl(QUrl(services.REPOSITORY)))
        body = QWidget()
        self.setCentralWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        header = QHBoxLayout()
        mark = QLabel()
        mark.setPixmap(self.windowIcon().pixmap(32, 32))
        header.addWidget(mark)
        header.addWidget(self.label("Fixer Audio", "brand"))
        header.addStretch()
        self.update_button = self.button("● Nova versão", self.update_app)
        self.update_button.hide()
        header.addWidget(self.update_button)
        header.addWidget(self.label(f"AMD ReLive Utility   /   v{VERSION}", "muted"))
        layout.addLayout(header)
        layout.addWidget(self.label("", "stripe"))
        layout.addWidget(self.label("Seus arquivos. Prontos para usar.", "title"))
        layout.addWidget(self.label("Repare o áudio, remova tags ou prepare seus clipes para compartilhar.", "muted"))
        settings = QHBoxLayout()
        for title, name, values in [("O que você quer fazer?", "mode", engine.MODES), ("Formato do áudio", "audio_format", ["FLAC", "WAV", "MP3"])]:
            column = QVBoxLayout()
            column.addWidget(QLabel(title))
            combo = QComboBox()
            combo.addItems(values)
            combo.setAccessibleName(title)
            setattr(self, name, combo)
            column.addWidget(combo)
            settings.addLayout(column, 3 if name == "mode" else 1)
        layout.addLayout(settings)
        self.explanation = self.label("", "muted")
        self.explanation.setWordWrap(True)
        layout.addWidget(self.explanation)
        toolbar = QHBoxLayout()
        self.add = self.button("Adicionar arquivos", self.pick_files, QStyle.StandardPixmap.SP_FileIcon)
        self.remove = self.button("Remover selecionados", self.remove_files)
        self.clear = self.button("Limpar fila", self.clear_files)
        for button in (self.add, self.remove, self.clear):
            toolbar.addWidget(button)
        toolbar.addStretch()
        self.count = self.label("Arraste arquivos para esta janela", "muted")
        toolbar.addWidget(self.count)
        layout.addLayout(toolbar)
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Arquivo", "Tamanho", "Status"])
        for col in (0, 2):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 100)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(lambda index: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.files[index.row()].parent))))
        splitter.addWidget(self.table)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Os resultados e detalhes de erros aparecem aqui.")
        splitter.addWidget(self.log)
        splitter.setSizes([250, 80])
        layout.addWidget(splitter, 1)
        destination = QHBoxLayout()
        destination.addWidget(QLabel("Salvar em"))
        self.output = QLineEdit(str(self.settings.value("output", str(Path.home() / "Downloads"))))
        destination.addWidget(self.output, 1)
        self.browse = self.button("Escolher pasta", self.pick_output, QStyle.StandardPixmap.SP_DirIcon)
        destination.addWidget(self.browse)
        layout.addLayout(destination)
        self.overwrite = QCheckBox("Substituir originais ao limpar metadados (sem backup)")
        layout.addWidget(self.overwrite)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        bottom = QHBoxLayout()
        self.state = self.label("Adicione arquivos para começar.", "muted")
        bottom.addWidget(self.state, 1)
        bottom.addWidget(self.button("Abrir pasta", self.open_output))
        self.cancel = self.button("Cancelar", self.cancel_batch)
        self.cancel.setEnabled(False)
        bottom.addWidget(self.cancel)
        self.start = self.button("Processar fila", self.run_batch, QStyle.StandardPixmap.SP_MediaPlay)
        self.start.setObjectName("primary")
        bottom.addWidget(self.start)
        layout.addLayout(bottom)
        self.mode.currentIndexChanged.connect(self.mode_changed)
        self.mode_changed()
        self.statusBar().showMessage("FFmpeg disponível" if engine.tool("ffmpeg") else "Instale o FFmpeg em Ferramentas para começar")

    def mode_changed(self):
        index = self.mode.currentIndex()
        self.audio_format.setEnabled(index == 2)
        self.overwrite.setVisible(index == 1)
        self.explanation.setText([
            "Mantém o vídeo original e converte todas as faixas de áudio para AAC estéreo.",
            "Copia vídeo, áudio e legendas sem recodificar. Remove tags, capas, anexos e capítulos.",
            "Extrai a primeira faixa. FLAC e WAV preservam as amostras; MP3 usa compressão com perdas.",
            "Converte para H.264 e AAC estéreo. Há recodificação para ampliar a compatibilidade."][index])

    def busy(self):
        return self.batch is not None and self.batch.isRunning()

    def add_files(self, paths):
        if self.busy():
            return
        for value in paths:
            path = Path(value).resolve()
            if path.is_file() and path not in self.files:
                self.files.append(path)
                row = self.table.rowCount()
                self.table.insertRow(row)
                for col, text in enumerate([path.name, f"{path.stat().st_size / 1048576:.1f} MB", "Na fila"]):
                    item = QTableWidgetItem(text)
                    item.setToolTip(str(path))
                    self.table.setItem(row, col, item)
        self.count.setText(f"{len(self.files)} arquivo(s) na fila")

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Adicionar mídia", "", "Mídia (*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.wmv *.mp3 *.flac *.wav *.m4a *.aac *.ogg *.opus);;Todos os arquivos (*)")
        self.add_files(files)

    def remove_files(self):
        for row in sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True):
            self.files.pop(row)
            self.table.removeRow(row)
        self.count.setText(f"{len(self.files)} arquivo(s) na fila")

    def clear_files(self):
        self.files.clear()
        self.table.setRowCount(0)
        self.count.setText("Arraste arquivos para esta janela")

    def pick_output(self):
        path = QFileDialog.getExistingDirectory(self, "Pasta de saída", self.output.text())
        if path:
            self.output.setText(path)

    def open_output(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.output.text()))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self.busy():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.add_files([url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()])

    def run_batch(self):
        if self.tasks:
            self.state.setText("Aguarde a tarefa em segundo plano terminar.")
            return
        if not self.files:
            self.state.setText("Adicione pelo menos um arquivo.")
            return
        if not engine.tool("ffmpeg"):
            self.install_engine()
            return
        directory = Path(self.output.text())
        if not directory.is_dir():
            QMessageBox.warning(self, "Pasta inválida", "Escolha uma pasta de saída existente.")
            return
        overwrite = self.mode.currentIndex() == 1 and self.overwrite.isChecked()
        if overwrite and QMessageBox.question(self, "Substituir originais?", "Os arquivos serão substituídos após a limpeza, sem backup. Continuar?") != QMessageBox.StandardButton.Yes:
            return
        self.settings.setValue("output", str(directory))
        self.lock(True)
        self.log.clear()
        self.progress.setRange(0, 0)
        self.batch = Batch(list(self.files), directory, self.mode.currentIndex(), self.audio_format.currentText(), overwrite, self)
        self.batch.changed.connect(self.row_changed)
        self.batch.detail.connect(self.log.appendPlainText)
        self.batch.completed.connect(self.batch_done)
        self.batch.finished.connect(lambda: self.lock(False))
        self.batch.start()

    def lock(self, active):
        for widget in (self.mode, self.add, self.remove, self.clear, self.start, self.output, self.browse, self.overwrite):
            widget.setEnabled(not active)
        self.audio_format.setEnabled(not active and self.mode.currentIndex() == 2)
        self.cancel.setEnabled(active)

    def row_changed(self, row, text):
        self.table.item(row, 2).setText(text)
        self.state.setText(f"Arquivo {row + 1} de {len(self.files)} · {text}")

    def cancel_batch(self):
        if self.busy():
            self.batch.requestInterruption()
            self.cancel.setEnabled(False)
            self.state.setText("Cancelando…")

    def batch_done(self, good, bad):
        self.progress.setRange(0, 100)
        self.progress.setValue(100 if good and not bad else 0)
        self.state.setText(f"{good} concluído(s) · {bad} falha(s)" + (" · Cancelado" if self.batch.isInterruptionRequested() else ""))

    def task(self, function, callback, silent=False):
        task = Task(function, self)
        self.tasks.append(task)
        task.result.connect(callback)
        if not silent:
            task.error.connect(lambda error: QMessageBox.warning(self, "Não foi possível concluir", error))
        task.finished.connect(lambda: self.tasks.remove(task))
        task.start()

    def install_engine(self):
        if self.busy() or self.tasks:
            return
        if QMessageBox.question(self, "Instalar FFmpeg", "Baixar FFmpeg e FFprobe (aproximadamente 110 MB)? Não requer administrador.") == QMessageBox.StandardButton.Yes:
            self.statusBar().showMessage("Baixando e verificando FFmpeg…")
            self.task(services.install_ffmpeg, lambda result: self.statusBar().showMessage(result))

    def check_updates(self, manual=False):
        def received(asset):
            self.update_asset = asset
            self.update_button.setVisible(bool(asset))
            if manual and not asset:
                self.statusBar().showMessage("Você está na versão mais recente.")
        self.task(services.latest, received, silent=not manual)

    def update_app(self):
        if self.busy() or self.tasks or not self.update_asset:
            return
        if QMessageBox.question(self, "Nova versão disponível", "Baixar e abrir o instalador da nova versão?") == QMessageBox.StandardButton.Yes:
            self.statusBar().showMessage("Baixando e verificando atualização…")
            def ready(path):
                try:
                    os.startfile(path)
                    QTimer.singleShot(300, self.close)
                except OSError as error:
                    QMessageBox.warning(self, "Instalador", str(error))
            self.task(lambda: services.download_update(self.update_asset), ready)

    def closeEvent(self, event):
        if self.busy() or self.tasks:
            self.statusBar().showMessage("Aguarde a tarefa terminar ou cancele o processamento antes de fechar.")
            event.ignore()
            return
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

def main():
    if os.name == "nt":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SCamposs.FixerAudioAMD")
    app = QApplication(sys.argv)
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    for font in (root / 'fonts').glob('*.ttf'):
        QFontDatabase.addApplicationFont(str(font))
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    arrow = (root / 'assets/chevron-down.svg').as_posix()
    app.setStyleSheet(STYLE + f'QComboBox::down-arrow {{image:url("{arrow}");width:16px;height:16px;}}')
    window = Window()
    geometry = window.settings.value("geometry")
    if geometry:
        window.restoreGeometry(geometry)
    window.show()
    sys.exit(app.exec())
