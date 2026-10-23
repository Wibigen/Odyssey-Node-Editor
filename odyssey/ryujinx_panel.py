"""The 'Ryujinx' tab of the output panel (one-click install + launch) and its settings window."""
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget)

from . import ryujinx as R
from .config import save_config
from .icons import bind

OK, KO = '#4ecb8a', '#ef5b5b'


def _pick(edit, folder, title, flt=''):
    cur = edit.text() or str(Path.home())
    p = QFileDialog.getExistingDirectory(edit, title, cur) if folder else QFileDialog.getOpenFileName(edit, title, cur, flt)[0]
    if p: edit.setText(p)


def _row(edit, folder, title, flt=''):
    w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0); h.addWidget(edit, 1); b = QPushButton('Browse…'); b.clicked.connect(lambda: _pick(edit, folder, title, flt)); h.addWidget(b); return w


class RyujinxDialog(QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent); self.setWindowTitle('Ryujinx settings'); self.setMinimumWidth(640); self.cfg = cfg; v = QVBoxLayout(self)
        intro = QLabel('Odyssey Node Editor copies your compiled mod into Ryujinx\'s mod folder, then starts the game.\n'
                       'Ryujinx cannot start a game by its title ID: give the game file you normally open (.xci / .nsp / .nca / extracted folder).'); intro.setWordWrap(True); intro.setStyleSheet('color:#8a91a5'); v.addWidget(intro)
        f = QFormLayout(); v.addLayout(f)
        self.exe, self.data, self.game, self.mod, self.build, self.files, self.args = (QLineEdit('' if cfg.get(k) == R.OLD_DEFAULT else cfg.get(k, '')) for k in ('ryu_exe', 'ryu_data', 'ryu_game', 'ryu_mod', 'ryu_build', 'ryu_files', 'ryu_args'))
        self.exe.setPlaceholderText(r'C:\Ryujinx\Ryujinx.exe'); self.data.setPlaceholderText(r'C:\Users\you\AppData\Roaming\Ryujinx  (detected automatically)')
        self.game.setPlaceholderText('Super Mario Odyssey.xci'); self.mod.setPlaceholderText('MyOdysseyMod'); self.build.setPlaceholderText('empty = <project folder>/build'); self.files.setPlaceholderText('automatic: subsdkN from CMakeLists.txt + main.npdm'); self.files.setToolTip('Leave empty: the sdk file name (subsdk9...) is read from CMakeLists.txt (set(SUBSDKX subsdk9)) and main.npdm is added. Or list names yourself, separated by ;  (wildcards allowed).')
        self.args.setPlaceholderText('optional extra command-line options')
        self.exe.textChanged.connect(self.autodetect); self.files.setToolTip('Exact file names, separated by ;  - Default: subsdk9;main.npdm. With the default list, the number after subsdk is read from "set(SUBSDKX subsdk9)" in CMakeLists.txt (next to the build folder).')
        f.addRow('Ryujinx executable *', _row(self.exe, False, 'Ryujinx executable', 'Programs (*.exe);;All files (*)'))
        self.dstat = QLabel(); f.addRow('Ryujinx data folder *', _row(self.data, True, 'Ryujinx data folder (contains "mods")')); f.addRow('', self.dstat)
        f.addRow('Game file *', _row(self.game, False, 'Super Mario Odyssey game file', 'Switch games (*.xci *.nsp *.nca *.nro);;All files (*)'))
        f.addRow('Mod folder name *', self.mod); self.dest = QLabel(); self.dest.setWordWrap(True); self.dest.setStyleSheet('color:#8a91a5'); f.addRow('', self.dest)
        f.addRow('Build folder', _row(self.build, True, 'Folder with the compiled files')); f.addRow('Files to copy (optional)', self.files); f.addRow('Extra options', self.args)
        self.fs = QCheckBox('Start in fullscreen (-f)'); self.fs.setChecked(bool(cfg.get('ryu_fullscreen'))); v.addWidget(self.fs)
        self.others = QCheckBox('Turn the other mods off before starting the game (a backup of Ryujinx\'s mods.json is kept)'); self.others.setChecked(bool(cfg.get('ryu_disable_others', True))); v.addWidget(self.others)
        self.inst = QCheckBox('Copy the compiled files before starting the game'); self.inst.setChecked(bool(cfg.get('ryu_install_first', True))); v.addWidget(self.inst)
        self.comp = QCheckBox('Compile first (stops if the build fails)'); self.comp.setChecked(bool(cfg.get('ryu_compile_first'))); v.addWidget(self.comp)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); v.addWidget(bb)
        for w in (self.data, self.mod): w.textChanged.connect(self.refresh)
        if not self.data.text(): self.autodetect()
        self.refresh()

    def autodetect(self):
        if self.data.text().strip(): return
        d = R.detect_data(self.exe.text().strip())
        if d: self.data.setText(d)
        self.refresh()

    def refresh(self):
        d = self.data.text().strip(); ok = R.looks_like_data(R.norm(d)) if d else False
        if ok: self.dstat.setText('Ryujinx data folder found'); self.dstat.setStyleSheet(f'color:{OK}')
        elif d: self.dstat.setText('This folder does not look like Ryujinx data (no mods / Config.json inside)'); self.dstat.setStyleSheet(f'color:{KO}')
        else: self.dstat.setText('Not detected: enter it (Ryujinx: File > Open Ryujinx Folder shows where it is)'); self.dstat.setStyleSheet(f'color:{KO}')
        m = self.mod.text().strip()
        self.dest.setText(f'Files will go to: {Path(R.norm(d)) / "mods" / "contents" / R.TITLE_ID / m / "exefs"}' if d and m else '')

    def values(self):
        n = R.norm
        return dict(ryu_exe=n(self.exe.text()), ryu_data=n(self.data.text()), ryu_game=n(self.game.text()), ryu_mod=self.mod.text().strip(), ryu_build=(self.build.text().strip().strip('"') if self.build.text().strip().startswith('/') and not self.build.text().strip().startswith('//') else n(self.build.text())),
                    ryu_files=self.files.text().strip(), ryu_args=self.args.text().strip(), ryu_fullscreen=self.fs.isChecked(), ryu_disable_others=self.others.isChecked(), ryu_install_first=self.inst.isChecked(), ryu_compile_first=self.comp.isChecked())


class RyujinxPanel(QWidget):
    def __init__(self, win):
        super().__init__(); self.win = win; self.proc = None; v = QVBoxLayout(self); v.setContentsMargins(10, 8, 10, 8)
        row = QHBoxLayout(); v.addLayout(row)
        self.bGo = QPushButton(' Install mod and launch Ryujinx'); bind(self.bGo, 'play_fill', '#ffffff', 16); self.bGo.setObjectName('pri'); self.bInst, self.bRun, self.bOpen, self.bCfg = QPushButton('Install mod only'), QPushButton('Launch only'), QPushButton('Open mod folder'), QPushButton('Settings…')
        self.bBack = QPushButton('Re-enable other mods'); self.bBack.setToolTip("Put Ryujinx's mods.json back as it was before the first launch from here")
        for b in (self.bGo, self.bInst, self.bRun, self.bOpen, self.bBack): row.addWidget(b)
        row.addStretch(1); row.addWidget(self.bCfg)
        self.status = QLabel(); self.status.setWordWrap(True); v.addWidget(self.status)
        self.log = QPlainTextEdit(); self.log.setObjectName('log'); self.log.setReadOnly(True); v.addWidget(self.log, 1)
        self.bGo.clicked.connect(self.go); self.bInst.clicked.connect(lambda: self.do_install()); self.bRun.clicked.connect(lambda: self.do_launch()); self.bOpen.clicked.connect(self.open_mods); self.bBack.clicked.connect(self.reenable); self.bCfg.clicked.connect(self.settings)
        self.refresh()

    @property
    def cfg(self): return self.win.cfg

    def say(self, s): self.log.appendPlainText(s)

    def refresh(self):
        p = R.problems(self.cfg)
        if p: self.status.setText('To set up: ' + ' · '.join(p) + '.  Click "Settings…".'); self.status.setStyleSheet(f'color:{KO}')
        else:
            b = R.build_dir(self.cfg); n = len(R.find_files(b, self.cfg.get('ryu_files'))) if b else 0
            self.status.setText(f'Ready. Mod: {R.mod_dir(self.cfg) / "exefs"}   ·   {n} compiled file(s) in {b}' if n else f'Ready, but no compiled file in {b} yet: compile first.'); self.status.setStyleSheet(f'color:{OK if n else "#c98a2b"}')

    def settings(self):
        c = dict(self.cfg)
        if not c.get('ryu_data'): c['ryu_data'] = R.detect_data(c.get('ryu_exe', ''))
        d = RyujinxDialog(c, self)
        if d.exec(): self.cfg.update(d.values()); save_config(self.cfg); self.say('Settings saved.')
        self.refresh()

    def need(self, install=True, launch=True):
        c = self.cfg; miss = [m for m in R.problems(c) if (launch or 'executable' not in m and 'Game' not in m)]
        if not install: miss = [m for m in miss if 'data' not in m and 'Mod folder' not in m]
        if miss:
            self.say('Missing: ' + '; '.join(miss)); self.refresh()
            if QMessageBox.question(self, 'Ryujinx', 'Some settings are missing:\n\n• ' + '\n• '.join(miss) + '\n\nOpen the settings?') == QMessageBox.Yes: self.settings()
            return not [m for m in R.problems(self.cfg) if m in miss]
        return True

    def do_install(self):
        if not self.need(True, False): return False
        try: dest, names = R.install(self.cfg)
        except RuntimeError as e: self.say('' + str(e)); self.refresh(); return False
        self.say(f'Mod folder emptied, then copied {", ".join(names)} to {dest}'); self.refresh(); return True

    def do_launch(self):
        if not self.need(False, True): return False
        if self.cfg.get('ryu_disable_others', True):
            try:
                off = R.disable_others(self.cfg); self.say(f'Other mods turned off: {", ".join(off)}' if off else 'No other active mod.')
            except RuntimeError as e: self.say('' + str(e) + '\n  The game is started anyway.')
        try: a, p, log = R.launch(self.cfg)
        except RuntimeError as e: self.say('' + str(e)); return False
        self.say('Starting: ' + ' '.join(f'"{x}"' if ' ' in x else x for x in a)); self.proc = (p, log)
        QTimer.singleShot(3000, self.check_launch); return True

    def check_launch(self):
        """Three seconds later: is Ryujinx still there? (the old 'ok' only meant that the process had been created)"""
        p, log = self.proc; code = p.poll()
        if code is None: self.say(f'Ryujinx is running (pid {p.pid}).'); return
        try: tail = '\n'.join(Path(log).read_text('utf-8', 'replace').strip().splitlines()[-15:])
        except OSError: tail = ''
        self.say(f'Ryujinx closed right after starting (exit code {code}).' + (f'\n{tail}' if tail else '') + f'\nFull output: {log}\nTry the same command by hand in a terminal; check the game file path and the extra options.')

    def go(self):
        if not self.need(True, True): return
        def run():
            if (not self.cfg.get('ryu_install_first', True) or self.do_install()): self.do_launch()
        if self.cfg.get('ryu_compile_first'): self.say('Compiling first…'); self.win.build_then(run)
        else: run()

    def reenable(self):
        if not self.cfg.get('ryu_data'): self.say('Set the Ryujinx data folder first.'); return
        try: self.say('Other mods are back as they were.' if R.restore_others(self.cfg) else 'Nothing to restore (no backup of mods.json).')
        except RuntimeError as e: self.say('' + str(e))

    def open_mods(self):
        d = R.mod_dir(self.cfg) if self.cfg.get('ryu_data') and self.cfg.get('ryu_mod', '').strip() else None
        if d is None: self.say('Set the Ryujinx data folder and the mod folder name first.'); return self.settings()
        d.mkdir(parents=True, exist_ok=True); QDesktopServices.openUrl(QUrl.fromLocalFile(str(d)))
