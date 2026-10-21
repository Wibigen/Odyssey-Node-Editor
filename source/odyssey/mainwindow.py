"""Main window: node canvas, block palette, inspector, generated code, problems, build."""
import re
from pathlib import Path
from PySide6.QtCore import QPointF, QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QGuiApplication, QIcon, QKeySequence, QPainter, QPixmap, QRadialGradient
from PySide6.QtWidgets import (QDockWidget, QInputDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox,
                               QPlainTextEdit, QPushButton, QStackedWidget, QTabWidget, QWidget)

from .canvas import GraphScene, GraphView
from . import __version__
from .shells import wsl_distros
from .config import GRAPHF, decomp_ok, load_catalog, load_config, main_cpp_path, resource, save_config
from .function_dialog import FunctionDialog
from .graph import DEFAULT_INC, GRP, PRE, Graph, sample
from .setup_dialog import SetupDialog
from .widgets import BuildRunner, CppHighlighter, Inspector, Palette

ANSI = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
FILTER = 'Odyssey Nodes graph (*.odn *.json)'
BIG = 16777215


def app_icon():
    f = resource('assets/logo.png')
    if f.exists(): return QIcon(str(f))
    pm = QPixmap(64, 64); pm.fill(Qt.transparent); p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    g = QRadialGradient(24, 22, 36); g.setColorAt(0, QColor('#ff9a9e')); g.setColorAt(1, QColor('#e8484f')); p.setBrush(g); p.setPen(Qt.NoPen); p.drawEllipse(4, 4, 56, 56)
    p.setBrush(QColor('#ffffff')); p.drawRoundedRect(18, 26, 12, 12, 3, 3); p.drawRoundedRect(36, 26, 12, 12, 3, 3); p.drawRect(30, 31, 6, 2); p.end(); return QIcon(pm)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg, self.graph = load_config(), Graph(); self.graph.set_catalog(load_catalog()); self.file = None; self.hist, self.hi = [], -1; self.out_collapsed, self.out_h = False, 300
        self.setWindowTitle(f'Odyssey Nodes v{__version__}'); self.setWindowIcon(app_icon()); self.resize(1500, 920)
        self.scene = GraphScene(self.graph); self.view = GraphView(self.scene); self.view.setFocusPolicy(Qt.StrongFocus); self.setCentralWidget(self.view)
        self.runner = BuildRunner(); self.snap_t = QTimer(self, singleShot=True, interval=400); self.snap_t.timeout.connect(self.snapshot)
        self._docks(); self._actions(); self._wire(); self._load_start()
        self.tick = QTimer(self); self.tick.timeout.connect(self._status); self.tick.start(500)
        s = QSettings('OdysseyNodes', 'OdysseyNodes')
        if s.value('geom'): self.restoreGeometry(s.value('geom')); self.restoreState(s.value('state'))

    # ---------- construction ----------
    def _docks(self):
        self.pal = Palette(); self.insp = Inspector(self.graph)
        for title, w, area, name in (('Blocks', self.pal, Qt.LeftDockWidgetArea, 'dPal'), ('Inspector', self.insp, Qt.RightDockWidgetArea, 'dInsp')):
            d = QDockWidget(title, self); d.setObjectName(name); d.setWidget(w); d.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable); self.addDockWidget(area, d)
        self.pal.setMinimumWidth(240); self.insp.setMinimumWidth(340)
        self.tabs = QTabWidget(); self.code = QPlainTextEdit(); self.code.setObjectName('code'); self.code.setReadOnly(True); self.code.setLineWrapMode(QPlainTextEdit.NoWrap)
        CppHighlighter(self.code.document())
        self.incs = QPlainTextEdit(); self.incs.setObjectName('code'); self.incs.setPlainText(DEFAULT_INC)
        self.probs = QListWidget(); self.log = QPlainTextEdit(); self.log.setObjectName('log'); self.log.setReadOnly(True); self.log.setPlainText('No build started yet.')
        for w, t in ((self.code, 'C++ code'), (self.incs, 'Includes'), (self.probs, 'Problems'), (self.log, 'Build')): self.tabs.addTab(w, t)
        corner = QWidget(); h = QHBoxLayout(corner); h.setContentsMargins(0, 0, 6, 0)
        self.bWrite, self.bBuild, self.bCopy, self.bSaveCpp, self.bFold = QPushButton('Write to project'), QPushButton('▶ Compile'), QPushButton('Copy'), QPushButton('Save as…'), QPushButton('▾')
        self.bBuild.setObjectName('pri'); self.bFold.setToolTip('Collapse / expand the output panel (Ctrl+J)'); self.bFold.setFixedWidth(34)
        for b in (self.bWrite, self.bBuild, self.bCopy, self.bSaveCpp, self.bFold): h.addWidget(b)
        self.tabs.setCornerWidget(corner, Qt.TopRightCorner); self.stack = self.tabs.findChild(QStackedWidget)
        self.dock_out = QDockWidget('Output', self); self.dock_out.setObjectName('dOut'); self.dock_out.setTitleBarWidget(QWidget()); self.dock_out.setWidget(self.tabs)
        self.dock_out.setFeatures(QDockWidget.NoDockWidgetFeatures); self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_out); self.resizeDocks([self.dock_out], [300], Qt.Vertical)
        self.pill = QPushButton(); self.pill.setFlat(True); self.statusBar().addPermanentWidget(self.pill)
        self.zoomL, self.cntL, self.bst = QLabel(), QLabel(), QLabel()
        for b in (self.zoomL, self.cntL): b.setContentsMargins(8, 0, 8, 0); self.statusBar().addPermanentWidget(b)
        self.bst.setContentsMargins(8, 0, 8, 0); self.statusBar().addWidget(self.bst)

    def _act(self, text, fn, key=None, view_only=False):
        a = QAction(text, self); a.triggered.connect(lambda _=False: fn())
        if key: a.setShortcut(QKeySequence(key))
        if view_only: a.setShortcutContext(Qt.WidgetShortcut); self.view.addAction(a)
        return a

    def _actions(self):
        self.aNew, self.aOpen, self.aSave = self._act('New', self.new, 'Ctrl+N'), self._act('Open…', self.open, 'Ctrl+O'), self._act('Save as…', self.save_as, 'Ctrl+S')
        self.aWrite, self.aBuild = self._act('Write to project', self.write_project, 'Ctrl+E'), self._act('Compile', self.build, 'F5')
        self.aUndo, self.aRedo = self._act('Undo', lambda: self.hist_go(-1), 'Ctrl+Z'), self._act('Redo', lambda: self.hist_go(1), 'Ctrl+Y')
        self.aDup, self.aDel = self._act('Duplicate', self.scene.duplicate_selected, 'Ctrl+D', True), self._act('Delete', self.scene.delete_selected, 'Del', True)
        self.aAll = self._act('Select all', lambda: [i.setSelected(True) for i in self.scene.node_items.values()], 'Ctrl+A', True)
        self.aBrowse = self._act('Add game function…', lambda: self.browse(None), 'Ctrl+F')
        self.aFit, self.aZin, self.aZout = self._act('Fit view', self.view.fit, 'F'), self._act('Zoom in', lambda: self.view.zoom_by(1.2), 'Ctrl++'), self._act('Zoom out', lambda: self.view.zoom_by(1 / 1.2), 'Ctrl+-')
        self.aFold = self._act('Show / hide output panel', self.toggle_output, 'Ctrl+J')
        self.aCfg, self.aAbout, self.aQuit = self._act('Settings…', self.configure, 'Ctrl+,'), self._act('About / credits', self.about), self._act('Quit', self.close, 'Ctrl+Q')
        mb = self.menuBar()
        for title, acts in (('File', [self.aNew, self.aOpen, self.aSave, None, self.aWrite, None, self.aQuit]), ('Edit', [self.aUndo, self.aRedo, None, self.aBrowse, self.aDup, self.aDel, self.aAll]),
                            ('View', [self.aFit, self.aZin, self.aZout, None, self.aFold]), ('Tools', [self.aBuild, self.aCfg]), ('Help', [self.aAbout])):
            m = mb.addMenu(title)
            for a in acts: m.addSeparator() if a is None else m.addAction(a)
        tb = self.addToolBar('Main'); tb.setObjectName('tb'); tb.setMovable(False)
        for a in (self.aNew, self.aOpen, self.aSave, None, self.aUndo, self.aRedo, None, self.aBrowse, self.aFit, None, self.aWrite, self.aBuild, None, self.aCfg): tb.addSeparator() if a is None else tb.addAction(a)

    def _wire(self):
        s = self.scene; s.changed.connect(self.on_changed); s.moved.connect(lambda: self.snap_t.start()); s.picked.connect(self.insp.show_node)
        s.node_activated.connect(self.edit_node); s.empty_double.connect(lambda pos: self.browse(pos)); s.empty_menu.connect(self.empty_menu)
        self.insp.changed.connect(self.field_changed); self.insp.valuechanged.connect(self.value_changed); self.insp.action.connect(self.inspector_action)
        self.pal.add_pre.connect(lambda n: self.add_pre(n, None)); self.pal.browse.connect(lambda: self.browse(None)); self.view.dropped.connect(self.dropped)
        self.incs.textChanged.connect(self.includes_changed); self.probs.itemDoubleClicked.connect(self.goto_problem)
        self.bWrite.clicked.connect(self.write_project); self.bBuild.clicked.connect(self.build); self.bFold.clicked.connect(lambda: self.toggle_output())
        self.bCopy.clicked.connect(lambda: (QGuiApplication.clipboard().setText(self.code.toPlainText()), self.statusBar().showMessage('Code copied', 3000)))
        self.bSaveCpp.clicked.connect(self.save_cpp); self.pill.clicked.connect(self.configure); self.runner.output.connect(self.log_out); self.runner.done.connect(self.build_done)
        self.tabs.tabBarClicked.connect(lambda _: self.toggle_output(False)); self.tabs.tabBarDoubleClicked.connect(lambda _: self.toggle_output())

    def _load_start(self):
        try: self.graph.load_json(GRAPHF.read_text('utf-8'))
        except Exception: self.graph.clear(); sample(self.graph)
        self.incs.blockSignals(True); self.incs.setPlainText(self.graph.inc); self.incs.blockSignals(False)
        self.scene.rebuild(keep=[]); self.refresh_code(); self.snapshot(); QTimer.singleShot(0, self.view.fit)
        if not load_catalog() or not decomp_ok(self.cfg): QTimer.singleShot(200, self.configure)

    # ---------- state ----------
    def _status(self):
        n = len(self.graph.cat); self.pill.setText(f'{n} functions' if n else '⚠ catalog missing'); self.pill.setStyleSheet('' if n else 'color:#ef5b5b')
        self.zoomL.setText(f'{self.view.zoom_percent()} %'); self.cntL.setText(f'{len(self.graph.nodes)} nodes · {len(self.graph.edges)} links')

    def toggle_output(self, collapse=None):
        collapse = (not self.out_collapsed) if collapse is None else collapse
        if collapse == self.out_collapsed: return
        if collapse:
            self.out_h = self.dock_out.height(); self.stack.hide()
            h = max(self.tabs.tabBar().sizeHint().height(), self.tabs.cornerWidget().sizeHint().height()) + 10; self.dock_out.setMinimumHeight(h); self.dock_out.setMaximumHeight(h)
        else:
            self.stack.show(); self.dock_out.setMinimumHeight(0); self.dock_out.setMaximumHeight(BIG); self.resizeDocks([self.dock_out], [max(self.out_h, 220)], Qt.Vertical)
        self.out_collapsed = collapse; self.bFold.setText('▴' if collapse else '▾')

    def refresh_code(self):
        try: txt = self.graph.gen()
        except Exception as e: txt = f'// Generation error: {e}'
        sb = self.code.verticalScrollBar(); v = sb.value(); self.code.setPlainText(txt); sb.setValue(v)
        self.probs.clear()
        for lvl, nid, msg in self.graph.problems():
            it = QListWidgetItem(('✖ ' if lvl == 'err' else '⚠ ') + msg); it.setData(Qt.UserRole, nid); it.setForeground(QColor('#ef5b5b' if lvl == 'err' else '#e6b673')); self.probs.addItem(it)
        self.tabs.setTabText(2, f'Problems ({self.probs.count()})' if self.probs.count() else 'Problems')

    def on_changed(self):
        self.refresh_code(); self.snap_t.start()
        if self.insp.nid and self.insp.nid not in self.graph.nodes: self.insp.show_node(0)
        else: self.insp.refresh()

    def field_changed(self): self.scene.rebuild(keep=[self.insp.nid]); self.on_changed()
    def value_changed(self): self.scene.rebuild(keep=[self.insp.nid]); self.refresh_code(); self.snap_t.start()
    def includes_changed(self): self.graph.inc = self.incs.toPlainText(); self.refresh_code(); self.snap_t.start()

    def snapshot(self):
        s = self.graph.to_json()
        if self.hi >= 0 and self.hist[self.hi] == s: return
        self.hist = (self.hist[:self.hi + 1] + [s])[-80:]; self.hi = len(self.hist) - 1
        try: GRAPHF.write_text(s, 'utf-8')
        except Exception: pass

    def hist_go(self, d):
        self.snapshot(); i = self.hi + d
        if 0 <= i < len(self.hist): self.hi = i; self.load_state(self.hist[i])

    def load_state(self, s):
        self.graph.load_json(s); self.incs.blockSignals(True); self.incs.setPlainText(self.graph.inc); self.incs.blockSignals(False)
        self.scene.rebuild(keep=[]); self.insp.show_node(0); self.refresh_code()

    # ---------- adding / editing nodes ----------
    def center(self): return self.view.mapToScene(self.view.viewport().rect().center()) + QPointF(-100 + (len(self.graph.nodes) % 5) * 24, -40 + (len(self.graph.nodes) % 5) * 24)

    def _place(self, type_, f, pos, d=None):
        pos = pos or self.center(); n = self.graph.add(type_, f, pos.x(), pos.y(), d); self.scene.commit(keep=[n.id]); self.insp.show_node(n.id)

    def add_pre(self, name, pos): t, f = PRE[name][:2]; self._place(t, dict(f), pos)

    def browse(self, pos=None):
        if not self.graph.cat:
            QMessageBox.information(self, 'Game functions', 'The function catalog is empty. Open Settings and extract it from OdysseyDecomp first.'); self.configure(); return
        dlg = FunctionDialog(list(self.graph.cat.values()), self)
        if dlg.exec(): t, f, d = dlg.result(); self._place(t, f, pos, d)

    def edit_node(self, nid):
        n = self.graph.nodes.get(nid)
        if not n: return
        if n.type in ('hook', 'callgame'):
            dlg = FunctionDialog(list(self.graph.cat.values()), self, node=n, graph=self.graph)
            if dlg.exec():
                t, f, d = dlg.result(); n.f.update(f)
                if t == 'callgame': n.d = d
                self.scene.commit(keep=[nid]); self.insp.show_node(nid)
        else: self.scene.select_only(nid); self.insp.show_node(nid)

    def dropped(self, text, pos):
        _, kind, val = text.split(':', 2)
        if kind == 'pre' and val in PRE: self.add_pre(val, pos)

    def empty_menu(self, pos, screen):
        m = QMenu(self); m.addAction('Game function…  (Ctrl+F)', lambda: self.browse(pos)); m.addSeparator()
        for cat, names in GRP.items():
            sm = m.addMenu(cat)
            for k in names: sm.addAction(k, lambda _=False, k=k: self.add_pre(k, pos))
        m.exec(screen)

    def inspector_action(self, k):
        nid = self.insp.nid
        if nid not in self.graph.nodes: return
        if k == 'edit': self.edit_node(nid); return
        self.scene.select_only(nid)
        {'dup': self.scene.duplicate_selected, 'del': self.scene.delete_selected, 'unlink': lambda: self.scene.unlink(nid)}[k]()
        ids = self.scene.selected_ids(); self.insp.show_node(ids[0] if len(ids) == 1 else 0)

    def goto_problem(self, it):
        nid = it.data(Qt.UserRole); w = self.scene.node_items.get(nid)
        if w: self.scene.select_only(nid); self.view.centerOn(w); self.insp.show_node(nid)

    # ---------- files ----------
    def new(self):
        if QMessageBox.question(self, 'New graph', 'Clear the current graph?') != QMessageBox.Yes: return
        self.graph.clear(); sample(self.graph); self.file = None; self.scene.rebuild(keep=[]); self.insp.show_node(0); self.refresh_code(); self.snapshot(); self.view.fit()

    def open(self):
        p, _ = QFileDialog.getOpenFileName(self, 'Open a graph', '', FILTER)
        if not p: return
        try: self.load_state(Path(p).read_text('utf-8'))
        except Exception as e: QMessageBox.critical(self, 'Cannot open file', str(e)); return
        self.file = p; self.snapshot(); self.view.fit(); self.statusBar().showMessage(f'Opened: {p}', 4000)

    def save_as(self):
        p, _ = QFileDialog.getSaveFileName(self, 'Save the graph', self.file or 'my_mod.odn', FILTER)
        if p: Path(p).write_text(self.graph.to_json(), 'utf-8'); self.file = p; self.statusBar().showMessage(f'Saved: {p}', 4000)

    def save_cpp(self):
        p, _ = QFileDialog.getSaveFileName(self, 'Save the code', 'main.cpp', 'C++ (*.cpp *.hpp *.h)')
        if p:
            with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(self.code.toPlainText())

    def write_project(self):
        p = main_cpp_path(self.cfg)
        if not p: QMessageBox.information(self, 'Write to project', 'Set your exlaunch project in Settings first.'); self.configure(); return False
        if Path(p).suffix.lower() not in ('.cpp', '.hpp', '.h'): QMessageBox.warning(self, 'Write to project', 'The generated file must end in .cpp, .hpp or .h.'); return False
        if not Path(p).parent.is_dir(): QMessageBox.warning(self, 'Write to project', f'Folder not found: {Path(p).parent}'); return False
        txt = self.code.toPlainText()
        with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(txt)
        self.statusBar().showMessage(f'Written: {p} ({len(txt.encode())} bytes)', 5000); return True

    # ---------- build ----------
    def build(self):
        if self.runner.running(): self.runner.stop(); return
        if not self.cfg['build_cmd']: QMessageBox.information(self, 'Compile', 'The build command is empty: see Settings.'); self.configure(); return
        if not self.cfg.get('build_env') and not self.ask_env(): return
        env, cwd = self.cfg['build_env'], self.cfg['project_dir'] or None
        if cwd and not (env == 'wsl' and cwd.startswith('/')) and not Path(cwd).is_dir(): QMessageBox.warning(self, 'Compile', f'Project folder not found: {cwd}'); return
        if not self.write_project(): return
        self.toggle_output(False); self.tabs.setCurrentWidget(self.log); self.log.clear(); self.log.appendPlainText(f'[{env}{" · " + self.cfg.get("wsl_distro", "") if env == "wsl" and self.cfg.get("wsl_distro") else ""}] $ {self.cfg["build_cmd"]}\n')
        self.bBuild.setText('■ Stop'); self.bst.setText('Build running…'); self.bst.setStyleSheet(''); self.runner.start(self.cfg['build_cmd'], cwd, env, self.cfg.get('wsl_distro', ''))

    def ask_env(self):
        """First compile on Windows: ask where the build tools live (WSL or Windows) and remember the answer."""
        box = QMessageBox(self); box.setWindowTitle('Compile'); box.setIcon(QMessageBox.Question)
        box.setText('Where do you build your exlaunch project?'); box.setInformativeText('WSL runs the command inside a Linux distribution (Ubuntu...). Windows runs it with cmd.exe. You can change this later in Settings.')
        bw = box.addButton('WSL (Linux)', QMessageBox.AcceptRole); bn = box.addButton('Windows (cmd)', QMessageBox.AcceptRole); box.addButton(QMessageBox.Cancel); box.exec(); c = box.clickedButton()
        if c is bn: self.cfg['build_env'] = 'windows'
        elif c is bw:
            ds = wsl_distros()
            if ds: d, ok = QInputDialog.getItem(self, 'WSL distribution', 'Which distribution builds the project?', ds, 0, True)
            else: d, ok = QInputDialog.getText(self, 'WSL distribution', 'No distribution found automatically. Name (empty = default):')
            if not ok: return False
            self.cfg.update(build_env='wsl', wsl_distro=d.strip())
        else: return False
        save_config(self.cfg); return True

    def log_out(self, s):
        self.log.moveCursor(self.log.textCursor().MoveOperation.End); self.log.insertPlainText(ANSI.sub('', s).replace('\r\n', '\n')); self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def build_done(self, code):
        self.bBuild.setText('▶ Compile'); ok = code == 0; self.bst.setText('Build succeeded ✔' if ok else f'Build failed (code {code})'); self.bst.setStyleSheet(f'color:{"#4ecb8a" if ok else "#ef5b5b"}')
        self.log.appendPlainText('\n' + self.bst.text()); self.statusBar().showMessage(self.bst.text(), 6000)

    # ---------- misc ----------
    def configure(self):
        d = SetupDialog(self.cfg, self); d.catalog_ready.connect(self.catalog_ready)
        if d.exec(): self.cfg = d.cfg
        else: self.cfg = load_config()
        self.refresh_code()

    def catalog_ready(self, cat): self.graph.set_catalog(cat); self.scene.rebuild(); self.refresh_code()

    def about(self):
        QMessageBox.about(self, 'Odyssey Nodes', f'<b>Odyssey Nodes</b> v{__version__}: a node editor that generates exlaunch C++ (Super Mario Odyssey 1.0.0).<br><br>Credits: OdysseyDecomp (MonsterDruide1 and contributors), exlaunch (shadowninja108), '
                          'sead and nnheaders (open-ead), Qt for Python (PySide6). Inspired by Unreal Engine Blueprints.<br>Unofficial mod tool, not affiliated with Nintendo.')

    def closeEvent(self, ev):
        self.snapshot(); self.runner.stop(); s = QSettings('OdysseyNodes', 'OdysseyNodes'); s.setValue('geom', self.saveGeometry()); s.setValue('state', self.saveState()); super().closeEvent(ev)
