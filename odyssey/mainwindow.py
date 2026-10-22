"""Main window: node canvas, block palette, inspector, generated code, problems, build."""
import os, re, time
from pathlib import Path
from PySide6.QtCore import QPointF, QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QGuiApplication, QIcon, QKeySequence, QPainter, QPixmap, QRadialGradient, QTextCursor, QTextFormat
from PySide6.QtWidgets import (QDockWidget, QInputDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox,
                               QPlainTextEdit, QPushButton, QStackedWidget, QTabWidget, QTextEdit, QWidget, QApplication)

from .canvas import GraphScene, GraphView
from . import __version__
from .shells import wsl_distros
from . import library, layout
from .config import DEFAULTS, GRAPHF, STARTF, decomp_ok, load_catalog, load_config, main_cpp_path, resource, save_config
from .cppimport import import_cpp
from .library_dialog import LibraryDialog
from .prefs_dialog import PrefsDialog
from .theme import apply_theme
from .function_dialog import FunctionDialog
from .group_dialog import GroupDialog
from .findbar import FindBar
from .ryujinx_panel import RyujinxPanel
from .graph import CATEGORIES, DEFAULT_INC, E, GRP, PRE, Graph, sample
from .setup_dialog import SetupDialog
from .widgets import BuildRunner, CodeEdit, CppHighlighter, Inspector, Palette

ANSI = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
FILTER_SAVE = 'Odyssey Node Editor graph (*.odn)'
FILTER_OPEN = 'Odyssey Node Editor graph (*.odn *.json);;All files (*)'  # .json = graphs saved by older versions
CPP_FILTER = 'C++ source (*.cpp *.cc *.cxx *.hpp *.h);;All files (*)'
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
        self.cfg, self.graph = load_config(), Graph(); self.graph.set_catalog(load_catalog()); self.graph.overrides = self.cfg['ret_overrides']; self.graph.favorites = self.cfg['favorites']; self.hl_map, self.file = {}, None; self.hist, self.hi = [], -1; self.out_collapsed, self.out_h = False, 300
        self.setWindowTitle(f'Odyssey Node Editor v{__version__}'); self.setWindowIcon(app_icon()); self.resize(1500, 920)
        self.scene = GraphScene(self.graph); self.view = GraphView(self.scene); self.view.setFocusPolicy(Qt.StrongFocus); self.setCentralWidget(self.view)
        self.runner = BuildRunner(); self.snap_t = QTimer(self, singleShot=True, interval=400); self.snap_t.timeout.connect(self.snapshot)
        self._docks(); self._actions(); self._wire(); self._load_start(); self.apply_prefs(); self.pal.set_library(library.entries())
        self.tick = QTimer(self); self.tick.timeout.connect(self._status); self.tick.start(500)
        s = QSettings('OdysseyNodes', 'OdysseyNodes')
        if s.value('geom'): self.restoreGeometry(s.value('geom')); self.restoreState(s.value('state'))

    # ---------- construction ----------
    def _docks(self):
        self.pal = Palette(); self.insp = Inspector(self.graph)
        for title, w, area, name in (('Blocks', self.pal, Qt.LeftDockWidgetArea, 'dPal'), ('Inspector', self.insp, Qt.RightDockWidgetArea, 'dInsp')):
            d = QDockWidget(title, self); d.setObjectName(name); d.setWidget(w); d.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable); self.addDockWidget(area, d)
        self.pal.setMinimumWidth(240); self.insp.setMinimumWidth(340)
        self.tabs = QTabWidget(); self.code = CodeEdit(); self.code.setObjectName('code'); self.code.setReadOnly(True); self.code.setLineWrapMode(QPlainTextEdit.NoWrap)
        CppHighlighter(self.code.document())
        self.incs = QPlainTextEdit(); self.incs.setObjectName('code'); self.incs.setPlainText(DEFAULT_INC)
        self.probs = QListWidget(); self.log = QPlainTextEdit(); self.log.setObjectName('log'); self.log.setReadOnly(True); self.log.setPlainText('No build started yet.')
        self.ryu = RyujinxPanel(self); self.after_build = None
        for w, t in ((self.code, 'C++ code'), (self.incs, 'Includes'), (self.probs, 'Problems'), (self.log, 'Build'), (self.ryu, 'Ryujinx')): self.tabs.addTab(w, t)
        corner = QWidget(); h = QHBoxLayout(corner); h.setContentsMargins(0, 0, 6, 0)
        self.bSaveLog = QPushButton('Save log as…'); self.bCopyLog, self.bCopyErr = QPushButton('Copy log'), QPushButton('Copy errors'); self.bCopyLog.setToolTip('Copy the whole build console'); self.bCopyErr.setToolTip('Copy only the error / warning lines of the console')
        self.bRepair = QPushButton('🛠 Repair base'); self.bRepair.setToolTip('Delete the build folder and run cmake again (fixes a broken exlaunch build setup)')
        self.bWrite, self.bBuild, self.bCopy, self.bSaveCpp, self.bFold = QPushButton('Write to project'), QPushButton('▶ Compile'), QPushButton('Copy'), QPushButton('Save as…'), QPushButton('▾')
        self.bBuild.setObjectName('pri'); self.bFold.setToolTip('Collapse / expand the output panel (Ctrl+J)'); self.bFold.setFixedWidth(34)
        for b in (self.bCopyErr, self.bCopyLog, self.bSaveLog, self.bRepair, self.bWrite, self.bBuild, self.bCopy, self.bSaveCpp, self.bFold): h.addWidget(b)
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
        self.aBrowse = self._act('Add game function…', lambda: self.browse(None), 'Ctrl+Shift+F')
        self.aFind = self._act('Find in the graph…', lambda: self.find(), 'Ctrl+F')
        self.aFit, self.aZin, self.aZout = self._act('Fit view', self.view.fit, 'F'), self._act('Zoom in', lambda: self.view.zoom_by(1.2), 'Ctrl++'), self._act('Zoom out', lambda: self.view.zoom_by(1 / 1.2), 'Ctrl+-')
        self.aFold = self._act('Show / hide output panel', self.toggle_output, 'Ctrl+J')
        self.aCfg, self.aAbout, self.aQuit = self._act('Settings (project, build, catalog)…', self.configure, 'Ctrl+Shift+,'), self._act('About / credits', self.about), self._act('Quit', self.close, 'Ctrl+Q')
        self.aPrefs = self._act('Preferences…', self.preferences, 'Ctrl+,')
        self.aClear = self._act('Clear the graph…', self.clear_graph)
        self.aImport = self._act('Import C++ file…', self.import_cpp_file, 'Ctrl+I')
        self.aSaveStart, self.aClearStart = self._act('Save as startup graph', self.save_startup), self._act('Forget the startup graph', self.clear_startup)
        self.aGroup = self._act('Group selected nodes', self.group_selected, 'Ctrl+G', True); self.aUngroup = self._act('Remove selected nodes from their group', self.ungroup_selected, 'Ctrl+Shift+G', True)
        self.aNote, self.aArrange = self._act('Add comment…', lambda: self.add_note(None), 'Ctrl+Shift+C'), self._act('Arrange nodes automatically', self.arrange_all, 'Ctrl+L')
        self.aRepair = self._act('Repair exlaunch base (rebuild cmake)…', self.repair_base)
        self.aLibSave, self.aLibOpen = self._act('Save selection to library…', self.save_to_library), self._act('Open the library…', self.open_library)
        mb = self.menuBar()
        for title, acts in (('File', [self.aNew, self.aOpen, self.aSave, None, self.aImport, None, self.aSaveStart, self.aClearStart, None, self.aWrite, None, self.aQuit]),
                            ('Edit', [self.aUndo, self.aRedo, None, self.aClear, self.aFind, self.aBrowse, self.aDup, self.aDel, self.aAll, None, self.aGroup, self.aUngroup, self.aNote, self.aArrange]),
                            ('Library', [self.aLibSave, self.aLibOpen, 'LIB']),
                            ('View', [self.aFit, self.aZin, self.aZout, None, self.aFold]), ('Tools', [self.aBuild, self.aRepair, self.aCfg, self.aPrefs]), ('Help', [self.aAbout])):
            m = mb.addMenu(title)
            for a in acts:
                if a is None: m.addSeparator()
                elif a == 'LIB': m.addSeparator(); self.libMenu = m.addMenu('Insert from library'); self.libMenu.aboutToShow.connect(self.fill_lib_menu)
                else: m.addAction(a)
        tb = self.addToolBar('Main'); tb.setObjectName('tb'); tb.setMovable(False)
        for a in (self.aNew, self.aOpen, self.aSave, None, self.aUndo, self.aRedo, None, self.aBrowse, self.aGroup, self.aNote, self.aFit, self.aClear, None, self.aWrite, self.aBuild, None, self.aLibOpen, self.aPrefs): tb.addSeparator() if a is None else tb.addAction(a)

    def _wire(self):
        s = self.scene; s.changed.connect(self.on_changed); s.moved.connect(lambda: self.snap_t.start()); s.picked.connect(self.insp.show_node)
        self.fbar = FindBar(self.view); self.fbar.changed.connect(self.find_changed); self.fbar.step.connect(self.find_step); self.fbar.closed.connect(lambda: (self.scene.set_search(''), self.view.setFocus()))
        self.view.installEventFilter(self); s.link_dropped.connect(self.link_dropped); s.find_request.connect(self.find)
        s.node_activated.connect(self.edit_node); s.empty_double.connect(lambda pos: self.browse(pos)); s.empty_menu.connect(self.empty_menu)
        self.insp.changed.connect(self.field_changed); self.insp.valuechanged.connect(self.value_changed); self.insp.action.connect(self.inspector_action)
        s.group_edit.connect(self.rename_group); s.note_edit.connect(self.edit_note); s.request.connect(lambda k, _: self.group_selected() if k == 'group' else None); s.picked.connect(lambda nid: self.highlight(nid, True))
        self.pal.add_lib.connect(lambda p: self.insert_lib(p, None));
        self.pal.add_pre.connect(lambda n: self.add_pre(n, None)); self.pal.browse.connect(lambda: self.browse(None)); self.view.dropped.connect(self.dropped)
        self.incs.textChanged.connect(self.includes_changed); self.probs.itemDoubleClicked.connect(self.goto_problem)
        self.bWrite.clicked.connect(self.write_project); self.bBuild.clicked.connect(self.build); self.bFold.clicked.connect(lambda: self.toggle_output())
        self.bCopy.clicked.connect(lambda: (QGuiApplication.clipboard().setText(self.code.toPlainText()), self.statusBar().showMessage('Code copied', 3000)))
        self.bSaveCpp.clicked.connect(self.save_cpp); self.bCopyLog.clicked.connect(lambda: self.copy_log(False)); self.bCopyErr.clicked.connect(lambda: self.copy_log(True)); self.bSaveLog.clicked.connect(self.save_log); self.tabs.currentChanged.connect(self.tab_buttons); self.pill.clicked.connect(self.configure); self.runner.output.connect(self.log_out); self.runner.done.connect(self.build_done); self.tab_buttons()
        self.tabs.tabBarClicked.connect(lambda _: self.toggle_output(False)); self.tabs.tabBarDoubleClicked.connect(lambda _: self.toggle_output())

    def _load_start(self):
        mode = self.cfg.get('pref_startup', 'session'); self.graph.clear()
        try:
            if mode == 'session': self.graph.load_json(GRAPHF.read_text('utf-8'))
            elif mode == 'startup': self.graph.load_json(STARTF.read_text('utf-8'))
            elif mode == 'example': sample(self.graph)
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
        try: txt, self.hl_map = self.graph.gen_map()
        except Exception as e: txt, self.hl_map = f'// Generation error: {e}', {}
        sb = self.code.verticalScrollBar(); v = sb.value(); self.code.setPlainText(txt); sb.setValue(v); self.highlight(self.insp.nid, False)
        self.probs.clear()
        for lvl, nid, msg in self.graph.problems():
            it = QListWidgetItem({'err': '✖ ', 'warn': '⚠ '}.get(lvl, 'ℹ ') + msg); it.setData(Qt.UserRole, nid); it.setForeground(QColor({'err': '#ef5b5b', 'warn': '#e6b673'}.get(lvl, '#6aa7ff'))); self.probs.addItem(it)
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
        if self.cfg.get('pref_autosave', True):
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
        pos = pos or self.center(); n = self.graph.add(type_, f, pos.x(), pos.y(), d); self.scene.commit(keep=[n.id]); self.insp.show_node(n.id); return n

    def add_pre(self, name, pos): t, f = PRE[name][:2]; return self._place(t, dict(f), pos)

    def browse(self, pos=None):
        if not self.graph.cat:
            QMessageBox.information(self, 'Game functions', 'The function catalog is empty. Open Settings and extract it from OdysseyDecomp first.'); self.configure(); return
        dlg = FunctionDialog(list(self.graph.cat.values()), self, graph=self.graph)
        ok = dlg.exec(); save_config(self.cfg)  # favorites are saved even if the window is cancelled
        if ok: t, f, d = dlg.result(); return self._place(t, f, pos, d)

    def edit_node(self, nid):
        n = self.graph.nodes.get(nid)
        if not n: return
        if n.type in ('hook', 'callgame'):
            dlg = FunctionDialog(list(self.graph.cat.values()), self, node=n, graph=self.graph)
            ok = dlg.exec(); save_config(self.cfg)
            if ok:
                t, f, d = dlg.result(); n.f.update(f)
                if t == 'callgame': n.d = d
                self.scene.commit(keep=[nid]); self.insp.show_node(nid)
        else: self.scene.select_only(nid); self.insp.show_node(nid)

    def dropped(self, text, pos):
        _, kind, val = text.split(':', 2)
        if kind == 'pre' and val in PRE: self.add_pre(val, pos)
        elif kind == 'lib': self.insert_lib(val, pos)

    def eventFilter(self, o, ev):
        if o is self.view and ev.type() == ev.Type.Resize and hasattr(self, 'fbar') and self.fbar.isVisible(): self.fbar.place()
        return super().eventFilter(o, ev)

    def find(self, text=None):
        self.fbar.open_bar(text)

    def find_changed(self, text):
        hit = self.scene.set_search(text); self._hits = sorted(hit, key=lambda i: (self.graph.nodes[i].y, self.graph.nodes[i].x)); self._hit_i = -1; self.fbar.set_count(len(self._hits))

    def find_step(self, d):
        hits = getattr(self, '_hits', [])
        if not hits: return
        self._hit_i = (getattr(self, '_hit_i', -1) + d) % len(hits); it = self.scene.node_items.get(hits[self._hit_i])
        if it: self.scene.select_only(hits[self._hit_i]); self.view.centerOn(it); self.fbar.set_count(len(hits), self._hit_i + 1)

    def link_dropped(self, nid, pid, d, pos, screen):
        """A link was released on empty space: pick a block, it is created there and connected to the pin the link came from."""
        g = self.graph; src = g.pin_type(nid, pid, d); ex = src == E; scratch = Graph(); cats = {}
        for name, (t, f, cat, _) in PRE.items():
            sp = scratch.spec(scratch.add(t, dict(f), 0, 0)); pins = sp[1] if d == 'o' else sp[2]
            if any((p.type == E) == ex for p in pins): cats.setdefault(cat, []).append(name)
        m = QMenu(self); m.addAction('Game function…', lambda: self._drop_make(nid, pid, d, pos, None))
        for cat in CATEGORIES:
            if cat in cats:
                sm = m.addMenu(cat)
                for name in cats[cat]: sm.addAction(name, lambda _=False, name=name: self._drop_make(nid, pid, d, pos, name))
        m.exec(screen)

    def _drop_make(self, nid, pid, d, pos, name):
        g = self.graph; src = g.pin_type(nid, pid, d); where = pos if d == 'o' else QPointF(pos.x() - 220, pos.y())
        n = self.browse(where) if name is None else self.add_pre(name, where)
        if n is None or nid not in g.nodes: return
        pins = g.spec(n)[1] if d == 'o' else g.spec(n)[2]; ok = [p for p in pins if (p.type == E) == (src == E)]
        if not ok: return
        p = next((q for q in ok if q.type == src), None) or next((q for q in ok if q.type in ('', 'void*') or src in ('', 'void*')), None) or ok[0]
        if g.connect((nid, pid, d), (n.id, p.id, 'i' if d == 'o' else 'o')):
            if self.scene.autogroup:
                ga, gb = g.group_of(nid), g.group_of(n.id)
                if ga is not None and gb is None: g.add_to_group(ga, [n.id])
            self.scene.commit(keep=[n.id])

    def empty_menu(self, pos, screen):
        m = QMenu(self); m.addAction('Game function…  (Ctrl+Shift+F)', lambda: self.browse(pos)); m.addAction('Find in the graph…  (Ctrl+F)', lambda: self.find()); m.addAction('Comment here…', lambda: self.add_note(pos))
        if self.scene.selected_ids(): m.addAction('Group selected nodes  (Ctrl+G)', self.group_selected)
        m.addSeparator()
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
        if self.cfg.get('pref_confirm_new', True) and QMessageBox.question(self, 'New graph', 'Clear the current graph?' + ('\n\nYour startup graph will be loaded.' if STARTF.exists() else '')) != QMessageBox.Yes: return
        self.graph.clear(); self.graph.inc = DEFAULT_INC; self.file = None  # includes go back to the standard list (a startup graph brings its own)
        if self.cfg.get('pref_new', 'startup') == 'startup' and STARTF.exists():
            try: self.graph.load_json(STARTF.read_text('utf-8'))
            except Exception: self.graph.clear()  # unreadable startup graph: an empty one
        self.incs.blockSignals(True); self.incs.setPlainText(self.graph.inc); self.incs.blockSignals(False)
        self.scene.rebuild(keep=[]); self.insp.show_node(0); self.refresh_code(); self.snapshot(); self.view.fit()

    def clear_graph(self):
        """Remove every node, link, group and comment (the file name and the includes list are kept)."""
        if not self.graph.nodes and not self.graph.groups and not self.graph.notes: self.statusBar().showMessage('The graph is already empty', 3000); return
        if QMessageBox.question(self, 'Clear the graph', f'Remove all {len(self.graph.nodes)} nodes, the links, groups and comments?\n(Ctrl+Z brings them back.)') != QMessageBox.Yes: return
        inc = self.graph.inc; self.graph.clear(); self.graph.inc = inc
        self.scene.rebuild(keep=[]); self.insp.show_node(0); self.scene.changed.emit(); self.statusBar().showMessage('Graph cleared', 3000)

    def open(self):
        p, _ = QFileDialog.getOpenFileName(self, 'Open a graph', '', FILTER_OPEN)
        if not p: return
        try: self.load_state(Path(p).read_text('utf-8'))
        except Exception as e: QMessageBox.critical(self, 'Cannot open file', str(e)); return
        self.file = p; self.snapshot(); self.view.fit(); self.statusBar().showMessage(f'Opened: {p}', 4000)

    def save_as(self):
        start = str(Path(self.file).with_suffix('.odn')) if self.file else 'my_mod.odn'
        p, _ = QFileDialog.getSaveFileName(self, 'Save the graph', start, FILTER_SAVE)
        if p:
            p = str(Path(p).with_suffix('.odn'))  # graphs are always saved as .odn (.json is only read, for older files)
            Path(p).write_text(self.graph.to_json(), 'utf-8'); self.file = p; self.statusBar().showMessage(f'Saved: {p}', 4000)

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
        self.suggest_build_cmd()
        errs = [m for lvl, _, m in self.graph.problems() if lvl == 'err']
        if errs and QMessageBox.question(self, 'Compile', f'The graph has {len(errs)} error(s), for example:\n\n• ' + '\n• '.join(errs[:3]) + '\n\nCompile anyway?') != QMessageBox.Yes: self.tabs.setCurrentWidget(self.probs); return
        self.toggle_output(False); self.tabs.setCurrentWidget(self.log); self.log.clear()
        self.log.appendPlainText('Step 1/2: write the generated code into the project')
        if not self.write_project(): self.log.appendPlainText('  ✘ could not write the file: nothing was compiled.'); return
        p = main_cpp_path(self.cfg); self.log.appendPlainText(f'  ✔ {p}  ({len(self.code.toPlainText().splitlines())} lines)')
        where = f'{env}{" · " + self.cfg.get("wsl_distro", "") if env == "wsl" and self.cfg.get("wsl_distro") else ""}'
        self.log.appendPlainText(f'Step 2/2: build   [{where}]  in {cwd or "(current folder)"}\n$ {self.cfg["build_cmd"]}\n'); self.t0 = time.monotonic()
        self.bBuild.setText('■ Stop'); self.bst.setText('Build running…'); self.bst.setStyleSheet(''); self.runner.start(self.cfg['build_cmd'], cwd, env, self.cfg.get('wsl_distro', ''))

    def suggest_build_cmd(self):
        """Still on the default command although the project has a Makefile (the exlaunch template): offer 'make' once."""
        c, proj = self.cfg, self.cfg.get('project_dir', '')
        if c.get('build_cmd') != DEFAULTS['build_cmd'] or c.get('build_asked') or not proj: return
        try: has = (Path(proj) / 'Makefile').is_file()
        except OSError: has = False
        if has:
            c['build_asked'] = True
            if QMessageBox.question(self, 'Build command', 'Your project has a Makefile (the exlaunch template).\nUse "make" as the build command instead of "cmake --build build"?\n\n(You can change it later in Settings.)') == QMessageBox.Yes: c['build_cmd'] = 'make'
            save_config(c)

    def tab_buttons(self, *_):
        on = self.tabs.currentWidget() is self.log; self.bCopyLog.setVisible(on); self.bCopyErr.setVisible(on); self.bSaveLog.setVisible(on)
        for b in (self.bWrite, self.bBuild, self.bCopy, self.bSaveCpp, self.bRepair): b.setVisible(self.tabs.currentWidget() is not self.ryu)

    def save_log(self):
        p, _ = QFileDialog.getSaveFileName(self, 'Save the build log', 'build_log.txt', 'Text files (*.txt);;All files (*)')
        if p:
            with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(self.log.toPlainText())
            self.statusBar().showMessage(f'Log saved: {p}', 5000)

    def copy_log(self, errors_only):
        t = self.log.toPlainText()
        if errors_only:
            keys = re.compile(r'error|\bfailed\b|\*\*\*|undefined reference|fatal|warning|cannot|no such file|not found|<3>', re.I)
            t = '\n'.join(l for l in t.splitlines() if keys.search(l)) or '(no error lines found)'
        QGuiApplication.clipboard().setText(t); self.statusBar().showMessage('Copied ' + ('error lines' if errors_only else 'the console') + f' ({len(t)} characters)', 4000)

    def repair_base(self):
        """Delete <project>/build, then re-run cmake with the exlaunch toolchain."""
        if self.runner.running(): QMessageBox.information(self, 'Repair', 'A command is already running: stop it first.'); return
        if not self.cfg['project_dir']: QMessageBox.information(self, 'Repair', 'Set the exlaunch project folder in Settings first.'); self.configure(); return
        if not self.cfg.get('build_env') and not self.ask_env(): return
        env, cwd = self.cfg['build_env'], self.cfg['project_dir']
        if not (env == 'wsl' and cwd.startswith('/')) and not Path(cwd).is_dir(): QMessageBox.warning(self, 'Repair', f'Project folder not found: {cwd}'); return
        if QMessageBox.question(self, 'Repair exlaunch base', f'This DELETES the "build" folder of:\n{cwd}\n\nand runs:\ncmake -B build -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain.cmake\n\nContinue?') != QMessageBox.Yes: return
        cm = 'cmake -B build -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain.cmake'
        cmd = f'(if exist build rmdir /s /q build) & {cm}' if env == 'windows' or (env == '' and os.name == 'nt') else f'rm -rf build && {cm}'
        self.toggle_output(False); self.tabs.setCurrentWidget(self.log); self.log.clear(); self.log.appendPlainText(f'[repair · {env}] $ {cmd}\n')
        self.bBuild.setText('■ Stop'); self.bst.setText('Repair running…'); self.bst.setStyleSheet(''); self.runner.start(cmd, cwd, env, self.cfg.get('wsl_distro', ''))

    def build_then(self, cb):
        """Compile, then call cb() only if the build succeeded."""
        if self.runner.running(): return
        self.after_build = cb; self.build()
        if not self.runner.running(): self.after_build = None  # build() refused to start

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
        el = time.monotonic() - getattr(self, 't0', time.monotonic()); errs = [l.strip() for l in self.log.toPlainText().splitlines() if re.search(r'\berror\b|undefined reference|\*\*\*', l)]
        if not ok and errs: self.bst.setText(f'Build failed ({len(errs)} error line(s))')
        self.log.appendPlainText(f'\n{"✔ Build succeeded" if ok else "✘ Build failed (code " + str(code) + ")"} in {el:.1f}s')
        if not ok and errs: self.log.appendPlainText('Main errors:\n  ' + '\n  '.join(l[-200:] for l in errs[:5]) + '\n(use "Copy errors" to copy every error line)')
        elif ok: self.log.appendPlainText('Next step: Ryujinx tab > "Install mod and launch".')
        self.statusBar().showMessage(self.bst.text(), 6000)
        cb, self.after_build = self.after_build, None
        if cb and ok: cb()
        elif cb: self.ryu.say('✘ Build failed: the game was not started.')
        self.ryu.refresh()

    # ---------- preferences ----------
    def apply_prefs(self):
        c = self.cfg; qss = f'QPlainTextEdit{{font-size:{int(c["pref_code_size"])}pt}}'
        self.code.setStyleSheet(qss); self.incs.setStyleSheet(qss); self.log.setStyleSheet(qss)
        self.code.setLineWrapMode(QPlainTextEdit.WidgetWidth if c['pref_wrap'] else QPlainTextEdit.NoWrap)
        inst, cst = self.graph.install, self.graph.calls; self.graph.install, self.graph.calls = c.get('pref_install', 'symbol'), c.get('pref_calls', 'direct'); self.scene.autogroup = bool(c.get('pref_autogroup', True)); self.scene.dropmenu = bool(c.get('pref_dropmenu', True)); self.code.set_numbers(c.get('pref_linenumbers', True)); self.scene.links_top = bool(c.get('pref_links_top')); self.scene.apply_z(); self.view.show_grid = bool(c['pref_grid']); self.view.viewport().update(); self.scene.snap = bool(c['pref_snap'])
        if getattr(self, '_ui_px', None) != int(c['pref_ui_size']):
            self._ui_px = int(c['pref_ui_size']); apply_theme(QApplication.instance(), self._ui_px)
        if (inst, cst) != (self.graph.install, self.graph.calls): self.refresh_code()
        self.highlight(self.insp.nid, False)

    def preferences(self):
        d = PrefsDialog(self.cfg, self)
        if d.exec(): self.cfg.update(d.values()); save_config(self.cfg); self.apply_prefs(); self.statusBar().showMessage('Preferences saved', 3000)

    # ---------- code <-> node highlight ----------
    def highlight(self, nid, scroll=False):
        """Highlight (and scroll to) the generated lines of the selected node."""
        on = self.cfg.get('pref_highlight', True); lines = self.hl_map.get(nid, []) if (on and nid) else []; doc = self.code.document(); sels = []
        for ln in lines:
            blk = doc.findBlockByNumber(ln)
            if not blk.isValid(): continue
            s = QTextEdit.ExtraSelection(); s.format.setBackground(QColor(232, 72, 79, 85)); s.format.setProperty(QTextFormat.FullWidthSelection, True)
            cur = QTextCursor(blk); cur.clearSelection(); s.cursor = cur; sels.append(s)
        self.code.setExtraSelections(sels)
        if scroll and sels: self.code.setTextCursor(QTextCursor(doc.findBlockByNumber(lines[0]))); self.code.centerCursor()
        elif scroll and on and nid: self.statusBar().showMessage('This node produces no code (is it connected to a hook or a function?)', 4000)

    # ---------- startup graph ----------
    def save_startup(self):
        try: STARTF.write_text(self.graph.to_json(), 'utf-8'); self.statusBar().showMessage('Saved as your startup graph: File > New and the startup option now use it', 6000)
        except Exception as e: QMessageBox.critical(self, 'Startup graph', str(e))

    def clear_startup(self):
        STARTF.unlink(missing_ok=True); self.statusBar().showMessage('Startup graph removed: File > New shows the example again', 5000)

    # ---------- import a C++ file ----------
    def import_cpp_file(self):
        p, _ = QFileDialog.getOpenFileName(self, 'Import a C++ file', '', CPP_FILTER)
        if not p: return
        try: src = Path(p).read_text('utf-8', errors='replace')
        except Exception as e: QMessageBox.critical(self, 'Import', str(e)); return
        if not self.graph.cat: QMessageBox.information(self, 'Import', 'The function catalog is empty, so game function calls and hooks cannot be recognised (they will stay as custom code). Extract it in Settings for a better result.')
        g2, rep = import_cpp(src, self.graph)
        if not g2.nodes: QMessageBox.information(self, 'Import', 'Nothing could be imported from this file.'); return
        box = QMessageBox(self); box.setWindowTitle('Import C++'); box.setIcon(QMessageBox.Information); box.setText(f'{Path(p).name}: ' + rep[0])
        box.setInformativeText('Conversion is best effort: anything not understood is kept as custom code, comments are not kept.' + ('\n\n' + '\n'.join('• ' + r for r in rep[1:8]) if len(rep) > 1 else ''))
        bR, bA = box.addButton('Replace the current graph', QMessageBox.AcceptRole), box.addButton('Add to the current graph', QMessageBox.AcceptRole); box.addButton(QMessageBox.Cancel); box.exec(); c = box.clickedButton()
        if c is bR: self.load_state(g2.to_json()); self.file = None; self.snapshot(); self.view.fit()
        elif c is bA:
            r = self.scene.itemsBoundingRect(); pos = QPointF(r.left(), r.bottom() + 120) if self.graph.nodes else QPointF(0, 0)
            new, notes = library.insert(self.graph, library.fragment(g2, set(g2.nodes), Path(p).stem), pos.x(), pos.y()); self.scene.commit(keep=new)
            if new: self.view.centerOn(self.scene.node_items[new[0]])
            if notes: self.statusBar().showMessage('; '.join(notes), 8000)

    # ---------- library (saved functions / templates) ----------
    def save_to_library(self):
        sel = self.scene.selected_ids()
        if not sel: QMessageBox.information(self, 'Library', 'Select a function (or a few nodes) first.'); return
        roots = [i for i in sel if self.graph.nodes[i].type in ('func', 'hook')]; expand = bool(roots) and len(roots) == len(sel)
        default = self.graph.nodes[roots[0]].f.get('name') or self.graph.title(self.graph.nodes[roots[0]]) if roots else 'Template'
        what = 'Saves this function with everything it uses (its blocks, values, called functions, globals).' if expand else f'Saves the {len(sel)} selected node(s) as a template.'
        name, ok = QInputDialog.getText(self, 'Save to library', what + '\nName:', text=default)
        if not ok or not name.strip(): return
        if (library.LIBDIR / (library.safe_name(name) + library.EXT)).exists() and QMessageBox.question(self, 'Library', f'"{name}" already exists. Replace it?') != QMessageBox.Yes: return
        p = library.save(self.graph, sel, name.strip(), expand=expand); self.pal.set_library(library.entries()); self.statusBar().showMessage(f'Saved to your library: {p}', 6000)

    def open_library(self):
        d = LibraryDialog(self); d.insert_requested.connect(lambda p: self.insert_lib(p, None)); d.exec(); self.pal.set_library(library.entries())

    def fill_lib_menu(self):
        self.libMenu.clear(); es = library.entries()
        for p, name, desc, n in es: self.libMenu.addAction(f'{name}  ({n})', lambda _=False, p=str(p): self.insert_lib(p, None))
        if not es: self.libMenu.addAction('(empty)').setEnabled(False)

    def insert_lib(self, path, pos):
        try: frag = library.load(path)
        except Exception as e: QMessageBox.critical(self, 'Library', f'Cannot read {path}: {e}'); return
        pos = pos or self.center(); new, notes = library.insert(self.graph, frag, pos.x(), pos.y()); self.scene.commit(keep=new)
        self.statusBar().showMessage(f'Inserted {frag.get("name", "")}' + (' - ' + '; '.join(notes) if notes else ''), 7000)

    # ---------- groups, comments, layout ----------
    def group_selected(self):
        ids = self.scene.selected_ids()
        if not ids: self.statusBar().showMessage('Select some nodes first (drag a rectangle on the canvas)', 4000); return
        d = GroupDialog(self.graph, None, ids, self)
        if d.exec(): d.apply(); self.scene.commit(keep=ids)

    def ungroup_selected(self):
        ids = self.scene.selected_ids()
        for v in self.graph.groups.values(): v['nodes'] = [i for i in v['nodes'] if i not in ids]
        self.graph._gc(); self.scene.commit(keep=ids)

    def rename_group(self, gid):
        gr = self.graph.groups.get(gid)
        if not gr: return
        d = GroupDialog(self.graph, gid, (), self)
        if d.exec(): d.apply(); self.scene.commit()

    def add_note(self, pos):
        text, ok = QInputDialog.getMultiLineText(self, 'Comment', 'Text of the comment (it is never part of the generated code):')
        if ok and text.strip(): pos = pos or self.center(); self.graph.add_note(text.strip(), pos.x(), pos.y()); self.scene.commit()

    def edit_note(self, nid):
        nt = self.graph.notes.get(nid)
        if not nt: return
        text, ok = QInputDialog.getMultiLineText(self, 'Comment', 'Text of the comment (empty = delete it):', nt['text'])
        if not ok: return
        if text.strip(): nt['text'] = text.strip()
        else: self.graph.notes.pop(nid, None)
        self.scene.commit()

    def arrange_all(self):
        ids = self.scene.selected_ids(); sub = len(ids) >= 2; dx = dy = 0.0
        if sub: dx, dy = min(self.graph.nodes[i].x for i in ids), min(self.graph.nodes[i].y for i in ids)
        layout.apply(self.graph, ids if sub else None, dx, dy); self.scene.commit(keep=ids)
        if not sub: self.view.fit()

    # ---------- misc ----------
    def configure(self):
        d = SetupDialog(self.cfg, self); d.catalog_ready.connect(self.catalog_ready)
        if d.exec(): self.cfg = d.cfg
        else: self.cfg = load_config()
        self.graph.overrides = self.cfg['ret_overrides']; self.graph.favorites = self.cfg['favorites']; self.refresh_code()

    def catalog_ready(self, cat): self.graph.set_catalog(cat); self.scene.rebuild(); self.refresh_code()

    def about(self):
        QMessageBox.about(self, 'Odyssey Node Editor', f'<b>Odyssey Node Editor</b> v{__version__}: a node editor that generates exlaunch C++ (Super Mario Odyssey 1.0.0).<br><br>Credits: OdysseyDecomp (MonsterDruide1 and contributors), exlaunch (shadowninja108), '
                          'sead and nnheaders (open-ead), Qt for Python (PySide6). Inspired by Unreal Engine Blueprints.<br>Unofficial mod tool, not affiliated with Nintendo.')

    def closeEvent(self, ev):
        self.snapshot(); self.runner.stop(); s = QSettings('OdysseyNodes', 'OdysseyNodes'); s.setValue('geom', self.saveGeometry()); s.setValue('state', self.saveState()); super().closeEvent(ev)
