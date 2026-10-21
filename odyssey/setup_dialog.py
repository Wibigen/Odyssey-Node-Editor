"""Settings dialog: required folders, catalog extraction (in a thread), exlaunch project, build command."""
from pathlib import Path
from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (QComboBox, QDialog, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar,
                               QPushButton, QVBoxLayout, QWidget)

from .catalog import extract, find_demangler
from .shells import ENVS, default_env, wsl_distros
from .config import decomp_ok, load_catalog, main_cpp_path, save_config


class ExtractThread(QThread):
    progress = Signal(str)
    ok = Signal(list)
    fail = Signal(str)

    def __init__(self, cfg):
        super().__init__(); self.cfg = dict(cfg)

    def run(self):
        try: self.ok.emit(extract(self.cfg, self.progress.emit))
        except Exception as e: self.fail.emit(str(e))


def path_row(edit, folder=True, title=''):
    row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0); row.addWidget(edit); b = QPushButton('Browse…'); row.addWidget(b)
    def pick():
        cur = edit.text() or str(Path.home())
        p = QFileDialog.getExistingDirectory(edit, title, cur) if folder else QFileDialog.getOpenFileName(edit, title, cur, 'C++ (*.cpp *.hpp *.h);;All files (*)')[0]
        if p: edit.setText(p)
    b.clicked.connect(pick); w = QWidget(); w.setLayout(row); return w


class SetupDialog(QDialog):
    catalog_ready = Signal(list)

    def __init__(self, cfg, parent=None):
        super().__init__(parent); self.cfg = cfg; self.th = None; self.setWindowTitle('Settings'); self.setMinimumWidth(640)
        v = QVBoxLayout(self)
        g1 = QGroupBox('1 · OdysseyDecomp (required)'); f1 = QFormLayout(g1)
        f1.addRow(QLabel('Folder of the cloned repository: the function catalog and their addresses are extracted from it automatically.'))
        self.decomp = QLineEdit(cfg['decomp_dir']); f1.addRow('Folder', path_row(self.decomp, True, 'OdysseyDecomp folder'))
        row = QHBoxLayout(); self.bExt = QPushButton('Extract the catalog'); self.bExt.setObjectName('pri'); row.addWidget(self.bExt)
        self.bar = QProgressBar(); self.bar.setRange(0, 0); self.bar.setVisible(False); row.addWidget(self.bar, 1); self.msg = QLabel(''); row.addWidget(self.msg, 2); f1.addRow(row)
        g2 = QGroupBox('2 · exlaunch project (to write and compile)'); f2 = QFormLayout(g2)
        self.proj = QLineEdit(cfg['project_dir']); f2.addRow('Folder', path_row(self.proj, True, 'exlaunch project folder'))
        self.main = QLineEdit(cfg['main_cpp']); self.main.setPlaceholderText('empty = <project>/src/program/main.cpp'); f2.addRow('main.cpp', path_row(self.main, False, 'main.cpp file'))
        self.cmd = QLineEdit(cfg['build_cmd']); f2.addRow('Build command', self.cmd)
        self.env = QComboBox(); self.env.addItem('- choose -', '')
        for k, lab in ENVS: self.env.addItem(lab, k)
        self.env.setCurrentIndex(max(0, self.env.findData(cfg.get('build_env') or default_env()))); f2.addRow('Run the build in', self.env)
        self.distro = QComboBox(); self.distro.setEditable(True); self.distro.addItems(wsl_distros()); self.distro.setCurrentText(cfg.get('wsl_distro', ''))
        self.distro.setToolTip('Empty = your default WSL distribution'); self.distro_l = QLabel('WSL distribution'); f2.addRow(self.distro_l, self.distro)
        self.env.currentIndexChanged.connect(self._env_changed); self._env_changed()
        g3 = QGroupBox('Advanced'); f3 = QFormLayout(g3)
        self.dem = QLineEdit(cfg['demangler']); self.dem.setPlaceholderText('auto: devkitPro, llvm-cxxfilt, c++filt'); f3.addRow('Demangler', self.dem)
        self.flt = QLineEdit(cfg['filter']); f3.addRow('Filter (regex)', self.flt)
        self.st = QLabel(); self.st.setTextFormat(Qt.RichText)
        row2 = QHBoxLayout(); row2.addStretch(1); self.bSave = QPushButton('Save'); self.bSave.setObjectName('pri'); self.bClose = QPushButton('Close'); row2.addWidget(self.bSave); row2.addWidget(self.bClose)
        for w in (g1, g2, g3, self.st): v.addWidget(w)
        v.addLayout(row2)
        self.bExt.clicked.connect(self.run_extract); self.bSave.clicked.connect(self.save); self.bClose.clicked.connect(self.reject)
        for e in (self.decomp, self.proj, self.main, self.dem): e.textChanged.connect(self.refresh)
        self.refresh()

    def collect(self):
        self.cfg.update(decomp_dir=self.decomp.text().strip(), project_dir=self.proj.text().strip(), main_cpp=self.main.text().strip(),
                        build_cmd=self.cmd.text().strip(), build_env=self.env.currentData() or '', wsl_distro=self.distro.currentText().strip(), demangler=self.dem.text().strip(), filter=self.flt.text().strip()); return self.cfg

    def _env_changed(self):
        w = self.env.currentData() == 'wsl'; self.distro.setVisible(w); self.distro_l.setVisible(w)

    def refresh(self):
        c = self.collect(); n = len(load_catalog()); dm = find_demangler(c['demangler'])
        rows = [(decomp_ok(c), 'OdysseyDecomp folder is valid' if decomp_ok(c) else 'OdysseyDecomp: data/file_list.yml not found'),
                (bool(dm), f'Demangler: {dm}' if dm else 'Demangler not found (install devkitPro or LLVM, or set its path in Advanced)'),
                (n > 0, f'Catalog: {n} functions' if n else 'Catalog not extracted yet'),
                (bool(main_cpp_path(c)), f'Generated file: {main_cpp_path(c)}' if main_cpp_path(c) else 'Generated file not set (optional while editing)')]
        self.st.setText('<br>'.join(f'<span style="color:{"#4ecb8a" if ok else "#ef5b5b"}">{"✔" if ok else "✖"}</span> {t}' for ok, t in rows))

    def save(self):
        c = self.collect()
        if c['decomp_dir'] and not decomp_ok(c): QMessageBox.warning(self, 'Settings', 'Invalid OdysseyDecomp folder: data/file_list.yml not found.'); return False
        save_config(c); self.accept(); return True

    def run_extract(self):
        c = self.collect()
        if not decomp_ok(c): QMessageBox.warning(self, 'Extraction', 'Set a valid OdysseyDecomp folder first.'); return
        save_config(c); self.bExt.setEnabled(False); self.bar.setVisible(True)
        self.th = ExtractThread(c); self.th.progress.connect(self.msg.setText); self.th.ok.connect(self._ok); self.th.fail.connect(self._fail); self.th.start()

    def _end(self): self.bExt.setEnabled(True); self.bar.setVisible(False)

    def _ok(self, cat): self._end(); self.msg.setText(f'{len(cat)} functions extracted ✔'); self.catalog_ready.emit(cat); self.refresh()
    def _fail(self, e): self._end(); self.msg.setText(''); QMessageBox.critical(self, 'Extraction failed', e)
    def done(self, r):
        if self.th and self.th.isRunning(): self.th.wait()
        super().done(r)
