"""Main window: node canvas, block palette, inspector, generated code, problems, build."""
from .i18n import tr, tr_n
from . import i18n
import os, re, time
from pathlib import Path
from PySide6.QtCore import QPointF, QSettings, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QGuiApplication, QIcon, QKeySequence, QPainter, QPixmap, QRadialGradient, QTextCursor, QTextFormat
from PySide6.QtWidgets import (QToolBar, QFrame, QToolButton, QVBoxLayout, QSizePolicy, QDockWidget, QInputDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox,
                               QPlainTextEdit, QPushButton, QStackedWidget, QTabWidget, QTextEdit, QWidget, QApplication)

from .canvas import GraphScene, GraphView
from . import __version__
from .shells import wsl_distros
from . import library, layout
from .config import DEFAULTS, GRAPHF, STARTF, decomp_ok, load_catalog, load_config, main_cpp_path, resource, save_config
from .cppimport import import_cpp
from .library_dialog import LibraryDialog
from .prefs_dialog import PrefsDialog
from .theme import ACCENTS, C, PLUGIN_THEMES, apply_theme, set_theme, theme_choices
from .plugins import MANAGER
from .plugin_dialog import PluginExplorer
from .plugfn_dialog import PluginFunctionDialog
from .help_dialog import HelpDialog, builtin_topics
from . import basepatch_dialog as BD
from . import plugnodes as PN
from .shortcuts_dialog import ShortcutsDialog
from .icons import bind, icon
from . import icons
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
        self.cfg, self.graph = load_config(), Graph(); self.graph.set_catalog(load_catalog()); self.graph.overrides = self.cfg['ret_overrides']; self.graph.favorites = self.cfg['favorites']; self.hl_map, self.file, self.saved_json = {}, None, None; self.hist, self.hi = [], -1; self.out_collapsed, self.out_h = False, 300
        if not MANAGER.plugins: MANAGER.load_all(self.cfg.get('plugins_disabled', []), enabled=self.cfg.get('plugins_enabled', []), data=self.cfg.setdefault('plugin_data', {}))
        MANAGER.window = self; MANAGER.data = self.cfg.setdefault('plugin_data', {})
        self.setWindowTitle(tr('Odyssey Node Editor v{0}', __version__)); self.setWindowIcon(app_icon()); self.resize(1500, 920)
        self.scene = GraphScene(self.graph); self.view = GraphView(self.scene); self.view.setFocusPolicy(Qt.StrongFocus)
        box = QWidget(); bl = QVBoxLayout(box); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(0); self.gbar = QFrame(); self.gbar.setObjectName('gbar'); bl.addWidget(self.gbar); bl.addWidget(self.view, 1); self.setCentralWidget(box)
        self.runner = BuildRunner(); self.snap_t = QTimer(self, singleShot=True, interval=400); self.snap_t.timeout.connect(self.snapshot)
        self._docks(); self._actions(); self._wire(); self._load_start(); self.apply_prefs(); self.pal.set_library(library.entries())
        self.tick = QTimer(self); self.tick.timeout.connect(self._status); self.tick.start(500); self._status()
        s = QSettings('OdysseyNodes', 'OdysseyNodes')
        if s.value('geom'): self.restoreGeometry(s.value('geom')); self.restoreState(s.value('state'))
        for t in self.findChildren(QToolBar):  # a window toolbar left over from an older layout
            if t is not self.gbar: t.hide(); t.deleteLater()

    # ---------- construction ----------
    def _docks(self):
        self.pal = Palette(); self.insp = Inspector(self.graph)
        for title, w, area, name in (('Blocks', self.pal, Qt.LeftDockWidgetArea, 'dPal'), ('Inspector', self.insp, Qt.RightDockWidgetArea, 'dInsp')):
            d = QDockWidget(title, self); d.setObjectName(name); d.setWidget(w); d.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable); self.addDockWidget(area, d)
        self.pal.setMinimumWidth(240); self.insp.setMinimumWidth(340)
        self.tabs = QTabWidget(); self.code = CodeEdit(); self.code.setObjectName('code'); self.code.setReadOnly(True); self.code.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.hlt = CppHighlighter(self.code.document())
        self.incs = QPlainTextEdit(); self.incs.setObjectName('code'); self.incs.setPlainText(DEFAULT_INC)
        self.probs = QListWidget(); self.log = QPlainTextEdit(); self.log.setObjectName('log'); self.log.setReadOnly(True); self.log.setPlainText('No build started yet.')
        self.ryu = RyujinxPanel(self); self.after_build = None
        for w, t in ((self.code, 'C++ code'), (self.incs, 'Includes'), (self.probs, 'Problems'), (self.log, 'Build'), (self.ryu, 'Ryujinx')): self.tabs.addTab(w, t)
        corner = QWidget(); h = QHBoxLayout(corner); h.setContentsMargins(0, 0, 6, 0)
        self.bSaveLog = QPushButton('Save log as…'); self.bCopyLog, self.bCopyErr = QPushButton('Copy log'), QPushButton('Copy errors'); self.bCopyLog.setToolTip('Copy the whole build console'); self.bCopyErr.setToolTip('Copy only the error / warning lines of the console')
        self.bRepair = QPushButton('Repair base'); self.bRepair.setToolTip('Delete the build folder and run cmake again (fixes a broken exlaunch build setup)')
        self.bWrite, self.bBuild, self.bCopy, self.bSaveCpp, self.bFold = QPushButton('Write to project'), QPushButton('Compile'), QPushButton('Copy'), QPushButton('Save as…'), QPushButton()
        self.bBuild.setObjectName('pri'); self.build_state(False); self.fold_icon(); bind(self.bWrite, 'write', size=16); bind(self.bCopy, 'copy', size=16); bind(self.bSaveCpp, 'save', size=16); bind(self.bRepair, 'wrench', size=16); bind(self.bCopyLog, 'copy', size=16); bind(self.bCopyErr, 'copy', size=16); bind(self.bSaveLog, 'save', size=16)
        self.bFold.setToolTip('Collapse / expand the output panel (Ctrl+J)'); self.bFold.setFixedWidth(34)
        for b in (self.bCopyErr, self.bCopyLog, self.bSaveLog, self.bRepair, self.bWrite, self.bBuild, self.bCopy, self.bSaveCpp, self.bFold): h.addWidget(b)
        self.tabs.setCornerWidget(corner, Qt.TopRightCorner); self.stack = self.tabs.findChild(QStackedWidget)
        self.dock_out = QDockWidget('Output', self); self.dock_out.setObjectName('dOut'); self.dock_out.setTitleBarWidget(QWidget()); self.dock_out.setWidget(self.tabs)
        self.dock_out.setFeatures(QDockWidget.NoDockWidgetFeatures); self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_out); self.resizeDocks([self.dock_out], [300], Qt.Vertical)
        self.pill = QPushButton(); self.pill.setFlat(True); self.statusBar().addPermanentWidget(self.pill)
        self.zoomL, self.cntL, self.bst = QLabel(), QLabel(), QLabel()
        for b in (self.zoomL, self.cntL): b.setContentsMargins(8, 0, 8, 0); self.statusBar().addPermanentWidget(b)
        self.bst.setContentsMargins(8, 0, 8, 0); self.statusBar().addWidget(self.bst)
        self.madeL = QLabel('Made by <b>WibiDev</b>'); self.madeL.setContentsMargins(8, 0, 8, 0); self.statusBar().insertWidget(0, self.madeL)

    def _act(self, text, fn, key=None, view_only=False):
        a = QAction(text, self); a.triggered.connect(lambda _=False: fn())
        if key: a.setShortcut(QKeySequence(key))
        if view_only: a.setShortcutContext(Qt.WidgetShortcut); self.view.addAction(a)
        return a

    def _actions(self):
        self.aNew, self.aOpen, self.aSave = self._act('New', self.new, 'Ctrl+N'), self._act('Open…', self.open, 'Ctrl+O'), self._act('Save', self.save, 'Ctrl+S'); self.aSaveAs = self._act('Save as…', self.save_as, 'Ctrl+Shift+S')
        self.aWrite, self.aBuild = self._act('Write to project', self.write_project, 'Ctrl+E'), self._act('Compile', self.build, 'F5')
        self.aUndo, self.aRedo = self._act('Undo', lambda: self.hist_go(-1), 'Ctrl+Z'), self._act('Redo', lambda: self.hist_go(1), 'Ctrl+Y')
        self.aDup, self.aDel = self._act('Duplicate', self.scene.duplicate_selected, 'Ctrl+D', True), self._act('Delete', self.scene.delete_selected, 'Del', True)
        self.aAll = self._act('Select all', lambda: [i.setSelected(True) for i in self.scene.node_items.values()], 'Ctrl+A', True)
        self.aBrowse = self._act('Add game function…', lambda: self.browse(None), 'Ctrl+Shift+F')
        self.aFind = self._act('Find in the graph…', lambda: self.find(), 'Ctrl+F')
        self.aPlugFn = self._act('Add plugin function…', lambda: self.add_plugin_function(None), 'Ctrl+Shift+K')
        self.aFit, self.aZin, self.aZout = self._act('Fit view', self.view.fit, 'F'), self._act('Zoom in', lambda: self.view.zoom_by(1.2), 'Ctrl++'), self._act('Zoom out', lambda: self.view.zoom_by(1 / 1.2), 'Ctrl+-')
        self.aFold = self._act('Show / hide output panel', self.toggle_output, 'Ctrl+J')
        self.aCfg, self.aAbout, self.aQuit = self._act('Settings (project, build, catalog)…', self.configure, 'Ctrl+Shift+,'), self._act('About / credits', self.about), self._act('Quit', self.close, 'Ctrl+Q')
        self.aHelp = self._act('Tutorials…', lambda: self.open_help(), 'F1'); self.aTour = self._act('Interface tour…', self.start_tour)
        self.aPrefs = self._act('Preferences…', self.preferences, 'Ctrl+,')
        self.aPlugins, self.aShortcuts = self._act('Plugin explorer…', self.open_plugins, 'Ctrl+Shift+P'), self._act('Keyboard shortcuts…', self.edit_shortcuts)
        self.aPlugDir = self._act('Open the plugins folder', lambda: PluginExplorer.open_dir(__import__('odyssey.plugins', fromlist=['USER_DIR']).USER_DIR))
        self.aClear = self._act('Clear', self.clear_graph)
        self.aImport = self._act('Import C++ file…', self.import_cpp_file, 'Ctrl+I')
        self.aSaveStart, self.aClearStart = self._act('Save as startup graph', self.save_startup), self._act('Forget the startup graph', self.clear_startup)
        self.aGroup = self._act('Group selected nodes', self.group_selected, 'Ctrl+G', True); self.aUngroup = self._act('Remove selected nodes from their group', self.ungroup_selected, 'Ctrl+Shift+G', True)
        self.aNote, self.aArrange = self._act('Add comment…', lambda: self.add_note(None), 'Ctrl+Shift+C'), self._act('Arrange nodes automatically', self.arrange_all, 'Ctrl+L')
        self.aRepair = self._act('Repair exlaunch base (rebuild cmake)…', self.repair_base)
        self.aLibSave, self.aLibOpen = self._act('Save selection to library…', self.save_to_library), self._act('Open the library…', self.open_library)
        mb = self.menuBar()
        for title, acts in (('File', [self.aNew, 'TPL', self.aOpen, 'REC', self.aSave, self.aSaveAs, None, self.aImport, None, self.aSaveStart, self.aClearStart, None, self.aWrite, None, self.aQuit]),
                            ('Edit', [self.aUndo, self.aRedo, None, self.aClear, self.aFind, self.aBrowse, self.aPlugFn, self.aDup, self.aDel, self.aAll, None, self.aGroup, self.aUngroup, self.aNote, self.aArrange]),
                            ('Library', [self.aLibSave, self.aLibOpen, 'LIB']),
                            ('View', [self.aFit, self.aZin, self.aZout, None, self.aFold]), ('Tools', [self.aBuild, self.aRepair, self.aCfg, self.aPrefs, self.aShortcuts]), ('Plugins', [self.aPlugins, self.aPlugDir]), ('Help', [self.aHelp, self.aTour, self.aAbout])):
            m = mb.addMenu(title); m.setObjectName('menu.' + title)
            for a in acts:
                if a is None: m.addSeparator()
                elif a == 'REC': self.recentMenu = m.addMenu('Open recent'); self.recentMenu.aboutToShow.connect(self.fill_recent_menu)
                elif a == 'TPL': self.tplMenu = m.addMenu('New from template'); self.tplMenu.aboutToShow.connect(self.fill_template_menu)
                elif a == 'LIB': m.addSeparator(); self.libMenu = m.addMenu('Insert from library'); self.libMenu.aboutToShow.connect(self.fill_lib_menu)
                else: m.addAction(a)
        for a, nm in ((self.aNew, 'new'), (self.aOpen, 'open'), (self.aSave, 'save'), (self.aSaveAs, 'save'), (self.aUndo, 'undo'), (self.aRedo, 'redo'), (self.aBrowse, 'library'), (self.aPlugFn, 'func'), (self.aFind, 'search'), (self.aGroup, 'group'), (self.aNote, 'note'), (self.aFit, 'fit'),
                      (self.aClear, 'trash'), (self.aLibOpen, 'group'), (self.aPrefs, 'settings'), (self.aWrite, 'write'), (self.aBuild, 'play_fill'), (self.aCfg, 'settings'), (self.aRepair, 'wrench'), (self.aAbout, 'help'), (self.aHelp, 'help'), (self.aPlugins, 'plus'), (self.aShortcuts, 'settings'), (self.aPlugDir, 'open')): bind(a, nm, size=20)
        # graph icon bar: plain buttons in three groups (left / centre / right), no overflow chevron
        self.tips = tips = {self.aClear: 'Clear', self.aBrowse: 'Open the catalog', self.aFind: 'Find in graph'}
        def group(*acts):
            f = QWidget(); l = QHBoxLayout(f); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(4)
            for a in acts:
                if a is None:
                    v = QFrame(); v.setFrameShape(QFrame.VLine); v.setObjectName('gsep'); l.addSpacing(4); l.addWidget(v); l.addSpacing(4); continue
                a.setToolTip(tips.get(a, a.text().replace('…', '')) + (f"  ({a.shortcut().toString()})" if not a.shortcut().isEmpty() else ''))
                b = QToolButton(); b.setDefaultAction(a); b.setIconSize(QSize(22, 22)); b.setAutoRaise(True)
                b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon if a is self.aClear else Qt.ToolButtonIconOnly)
                b.setFixedSize(38 if a is not self.aClear else b.fontMetrics().horizontalAdvance(a.text()) + 22 + 40, 36); l.addWidget(b)
            return f
        gl, gc, gr = group(self.aNew, self.aOpen, self.aSave, None, self.aUndo, self.aRedo), group(self.aClear, self.aFit, self.aFind), group(self.aBrowse, self.aPrefs)
        bar = QHBoxLayout(self.gbar); bar.setContentsMargins(8, 4, 8, 4); bar.setSpacing(0)
        bar.addWidget(gl); bar.addStretch(1); bar.addWidget(gc); bar.addStretch(1); bar.addWidget(gr)
        wd = max(gl.sizeHint().width(), gr.sizeHint().width()); gl.setMinimumWidth(wd); gr.setMinimumWidth(wd)  # centre group stays centred
        gr.layout().setAlignment(Qt.AlignRight)
        vm = mb.findChild(QMenu, 'menu.View'); vm.addSeparator()
        self.lookMenu = vm.addMenu(icon('palette', size=16), 'Theme'); self.build_language_menu(); self.build_theme_menu(); self.build_plugin_menu(); self.build_help_menu(); self.init_shortcuts()

    def build_language_menu(self):
        """View > Language: the globe icon stays the same in every language, so it can always be found. The choice is applied at the next start."""
        self.langMenu = self.menuBar().findChild(QMenu, 'menu.View').addMenu(icon('globe', size=16), 'Language'); self.langMenu.setObjectName('menu.Language'); grp = QActionGroup(self); grp.setExclusive(True)
        cur = i18n.CUR
        for code, name in i18n.LANGS:
            a = self.langMenu.addAction(name); a.setCheckable(True); a.setChecked(code == cur); grp.addAction(a); a.triggered.connect(lambda _=False, c=code: self.choose_language(c))

    def choose_language(self, code):
        if code == i18n.CUR: return
        self.cfg['language'] = code; save_config(self.cfg)
        box = QMessageBox(QMessageBox.Question, i18n.tr_in(code, 'Language'), i18n.tr_in(code, 'The language changes the next time the program starts.\n\nRestart now?'), parent=self)
        yes, no = box.addButton(i18n.tr_in(code, 'Restart now'), QMessageBox.AcceptRole), box.addButton(i18n.tr_in(code, 'Later'), QMessageBox.RejectRole); box.exec()
        if box.clickedButton() is yes: self._restart = True; self.close()
        else: self.sync_language_menu()

    def sync_language_menu(self):
        for a, (code, _name) in zip(self.langMenu.actions(), i18n.LANGS): a.setChecked(code == i18n.CUR)

    def build_theme_menu(self):
        """View > Theme: built-in themes + the ones added by plugins; accent colors."""
        self.lookMenu.clear(); self.lookActs = {}; grp = QActionGroup(self); grp.setExclusive(True)
        for key, lab, base in theme_choices():
            a = self.lookMenu.addAction(icon('moon' if base == 'dark' else 'sun', size=16), lab); a.setCheckable(True); grp.addAction(a); a.triggered.connect(lambda _=False, m=key: self.set_look(mode=m)); self.lookActs[key] = a
        self.lookMenu.addSeparator(); self.accentMenu = self.lookMenu.addMenu('Accent color'); self.accentActs = {}; ag = QActionGroup(self); ag.setExclusive(True)
        for nm in ('Theme', *ACCENTS):
            a = self.accentMenu.addAction('Theme default' if nm == 'Theme' else nm); a.setCheckable(True); ag.addAction(a); a.triggered.connect(lambda _=False, n=nm: self.set_look(accent=n)); self.accentActs[nm] = a
        self.sync_look_menu()

    def theme_accent(self, name):
        t = PLUGIN_THEMES.get(self.cfg.get('pref_theme', 'dark')); return ACCENTS.get(name) or (t['accent'] if t and t['accent'] else ACCENTS['Red'])

    # ---------- plugins ----------
    def build_plugin_menu(self):
        """Plugins menu: explorer, then the actions plugins added with api.add_action, then the folder shortcut."""
        m = self.menuBar().findChild(QMenu, 'menu.Plugins'); m.clear(); m.addAction(self.aPlugins)
        for old in getattr(self, 'plugin_actions', []): self.removeAction(old)
        self.plugin_actions = []; first = True
        for pl in MANAGER.plugins:
            if not pl.enabled: continue
            for i, (label, fn, key) in enumerate(pl.actions):
                if first: m.addSeparator(); first = False
                a = QAction(f'{label}', self); a.setObjectName(f'plugin.{pl.id}.{i}'); a.setStatusTip(tr('{0} (plugin)', pl.title)); a.triggered.connect(lambda _=False, fn=fn: self.run_plugin_action(fn))
                if key: a.setShortcut(QKeySequence(key))
                m.addAction(a); self.plugin_actions.append(a)
        m.addSeparator(); m.addAction(self.aPlugDir)

    # ---------- help ----------
    def help_topics(self):
        """[(section, source, title, path, buttons)]: the editor's tutorials, then the pages of the enabled plugins."""
        return builtin_topics() + [('Plugin tutorials', pl.title, title, path, btn) for pl in MANAGER.plugins if pl.enabled for title, path, btn in pl.help]

    def build_help_menu(self):
        """Help menu: Tutorials (editor + plugins, in one window), Interface tour, About."""
        m = self.menuBar().findChild(QMenu, 'menu.Help'); m.clear(); m.addAction(self.aHelp); m.addAction(self.aTour); m.addSeparator(); m.addAction(self.aAbout)

    def open_help(self, start=0):
        topics = self.help_topics()
        if not topics: QMessageBox.information(self, 'Tutorials', 'No tutorial found (the tutorials folder is missing).'); return
        d = getattr(self, '_help', None)
        try:
            if d is not None and d.isVisible(): d.raise_(); d.activateWindow(); d.pick(start); return
        except RuntimeError: pass
        d = self._help = HelpDialog(topics, self, start); d.run.connect(self.run_help_action); d.show()

    def open_help_page(self, title):
        t = self.help_topics(); i = next((k for k, x in enumerate(t) if x[2] == title), 0); self.open_help(i)

    # ---------- interface tour ----------
    def start_tour(self, first_run=False):
        from .tour import Tour
        t = getattr(self, '_tour', None)
        try:
            if t is not None and t.isVisible(): return
        except RuntimeError: pass
        self._tour = Tour(self); self._tour.finished.connect(self.tour_finished); self._tour.start()

    def tour_finished(self, completed):
        """Completed or skipped: never shown again at startup. Closing the program in the middle leaves it unmarked, so it comes back."""
        self.cfg['tour_done'] = True; save_config(self.cfg)
        if completed and getattr(self._tour, 'open_tut', False): QTimer.singleShot(0, lambda: self.open_help())

    def maybe_first_tour(self):
        if not self.cfg.get('tour_done'): QTimer.singleShot(500, self.start_tour)

    def run_help_action(self, action):
        kind, _, arg = action.partition(':')
        if kind == 'template':
            for pl in MANAGER.plugins:
                if pl.enabled:
                    for name, path, desc in pl.templates:
                        if name == arg: self.new_from_template(path); return
            QMessageBox.information(self, 'Help', tr('The template "{0}" is not available (is its plugin enabled?).', arg))
        elif kind == 'browser': self.add_plugin_function(None, arg)
        elif kind == 'base':
            pl = MANAGER.get(arg)
            if pl and pl.enabled and pl.base: BD.BaseDialog(self, pl).exec()
            else: QMessageBox.information(self, 'Help', 'Enable the plugin first (Plugins > Plugin explorer).')
        elif kind == 'plugins': self.open_plugins()
        elif kind == 'tour': self.start_tour()
        elif kind == 'settings': self.configure()
        elif kind == 'open' and arg: self.open_help_page(arg)

    def run_plugin_action(self, fn):
        try: fn(self)
        except Exception as e: QMessageBox.warning(self, 'Plugin', f'{type(e).__name__}: {e}')

    def reload_plugins(self):
        MANAGER.load_all(self.cfg.get('plugins_disabled', []), enabled=self.cfg.get('plugins_enabled', []), window=self, data=self.cfg.setdefault('plugin_data', {}))

    def plugins_changed(self):
        """After the explorer reloaded the plugins: new palette, themes, menus, nodes of the open graph."""
        save_config(self.cfg); self.pal.rebuild(); self.pal.set_library(library.entries()); self._look = None; self.build_theme_menu(); self.build_plugin_menu(); self.build_help_menu(); self.init_shortcuts()
        self.apply_prefs(); self.scene.rebuild(); self.refresh_code(); self.refresh_problems() if hasattr(self, 'refresh_problems') else None

    def open_plugins(self):
        d = PluginExplorer(self.cfg, self.reload_plugins, self); d.changed.connect(self.plugins_changed); d.exec(); save_config(self.cfg)

    # ---------- keyboard shortcuts ----------
    def registry(self):
        """{id: QAction} of every command that can get a shortcut (menu commands + plugin actions)."""
        out = {k: v for k, v in vars(self).items() if k.startswith('a') and isinstance(v, QAction) and v.text().strip() and k != 'aPlugDir'}
        for a in getattr(self, 'plugin_actions', []): out[a.objectName()] = a
        return out

    def init_shortcuts(self):
        """Remember the built-in shortcuts, then apply the ones the user changed."""
        if not hasattr(self, 'sc_default'): self.sc_default = {}
        for k, a in self.registry().items(): self.sc_default.setdefault(k, a.shortcut().toString(QKeySequence.PortableText))
        self.apply_shortcuts()

    def apply_shortcuts(self):
        mine = self.cfg.get('shortcuts', {})
        for k, a in self.registry().items(): a.setShortcut(QKeySequence(mine.get(k, self.sc_default.get(k, '')), QKeySequence.PortableText))
        self.refresh_tips()

    def sk(self, a):
        s = a.shortcut().toString(QKeySequence.NativeText); return f'  ({s})' if s else ''

    def refresh_tips(self):
        tips = getattr(self, 'tips', {})
        for a in (self.aNew, self.aOpen, self.aSave, self.aUndo, self.aRedo, self.aClear, self.aFit, self.aFind, self.aBrowse, self.aPrefs):
            a.setToolTip(tips.get(a, a.text().replace('…', '')) + self.sk(a))

    def edit_shortcuts(self):
        reg = self.registry(); mine = self.cfg.get('shortcuts', {}); ent = [(k, a.text().replace('&', '').replace('…', '') + (' (plugin)' if k.startswith('plugin.') else ''), self.sc_default.get(k, ''), mine.get(k, self.sc_default.get(k, ''))) for k, a in reg.items()]
        ent.sort(key=lambda e: e[1].lower()); d = ShortcutsDialog(ent, self)
        if d.exec(): self.cfg['shortcuts'] = d.result(); save_config(self.cfg); self.apply_shortcuts(); self.statusBar().showMessage('Keyboard shortcuts saved', 3000)

    def _wire(self):
        s = self.scene; s.changed.connect(self.on_changed); s.moved.connect(lambda: self.snap_t.start()); s.picked.connect(self.insp.show_node)
        self.fbar = FindBar(self.view); self.fbar.changed.connect(self.find_changed); self.fbar.step.connect(self.find_step); self.fbar.closed.connect(lambda: (self.scene.set_search(''), self.view.setFocus()))
        self.view.installEventFilter(self); s.link_dropped.connect(self.link_dropped); s.find_request.connect(self.find)
        s.node_activated.connect(self.edit_node); s.empty_double.connect(lambda pos: self.browse(pos)); s.empty_menu.connect(self.empty_menu)
        self.insp.changed.connect(self.field_changed); self.insp.valuechanged.connect(self.value_changed); self.insp.action.connect(self.inspector_action)
        s.group_edit.connect(self.rename_group); s.note_edit.connect(self.edit_note); s.request.connect(lambda k, _: self.group_selected() if k == 'group' else None); s.picked.connect(lambda nid: self.highlight(nid, True))
        self.pal.add_lib.connect(lambda p: self.insert_lib(p, None));
        self.pal.add_pre.connect(lambda n: self.add_pre(n, None)); self.pal.browse.connect(lambda: self.browse(None)); self.pal.plugfn.connect(lambda: self.add_plugin_function(None)); self.view.dropped.connect(self.dropped)
        self.incs.textChanged.connect(self.includes_changed); self.probs.itemDoubleClicked.connect(self.goto_problem)
        self.bWrite.clicked.connect(self.write_project); self.bBuild.clicked.connect(self.build); self.bFold.clicked.connect(lambda: self.toggle_output())
        self.bCopy.clicked.connect(lambda: (QGuiApplication.clipboard().setText(self.code.toPlainText()), self.statusBar().showMessage('Code copied', 3000)))
        self.bSaveCpp.clicked.connect(self.save_cpp); self.bCopyLog.clicked.connect(lambda: self.copy_log(False)); self.bCopyErr.clicked.connect(lambda: self.copy_log(True)); self.bSaveLog.clicked.connect(self.save_log); self.tabs.currentChanged.connect(self.tab_buttons); self.pill.clicked.connect(self.configure); self.runner.output.connect(self.log_out); self.runner.done.connect(self.build_done); self.tab_buttons()
        self.tabs.tabBarClicked.connect(lambda _: self.toggle_output(False)); self.tabs.tabBarDoubleClicked.connect(lambda _: self.toggle_output())

    def _load_start(self):
        mode = self.cfg.get('pref_startup', 'session'); self.graph.clear()
        try:
            if mode == 'session':
                self.graph.load_json(GRAPHF.read_text('utf-8')); lf = self.cfg.get('last_file')
                if lf and Path(lf).is_file():  # the session belongs to a file: Ctrl+S keeps saving into it (the title shows if it has unsaved changes)
                    self.file = lf
                    try: g0 = Graph(); g0.load_json(Path(lf).read_text('utf-8')); self.saved_json = g0.to_json()
                    except Exception: self.file = None
            elif mode == 'startup': self.graph.load_json(STARTF.read_text('utf-8'))
            elif mode == 'example': sample(self.graph)
        except Exception: self.graph.clear(); sample(self.graph)
        self.incs.blockSignals(True); self.incs.setPlainText(self.graph.inc); self.incs.blockSignals(False)
        self.scene.rebuild(keep=[]); self.refresh_code(); self.snapshot(); QTimer.singleShot(0, self.view.fit)
        QTimer.singleShot(200, self._first_run)

    def _first_run(self):
        """After the window is shown: the setup dialog when the catalog is missing, then the interface tour the first time."""
        if not load_catalog() or not decomp_ok(self.cfg): self.configure()
        self.maybe_first_tour()

    # ---------- state ----------
    def _status(self):
        n = len(self.graph.cat); self.pill.setText(tr('{0} functions', n) if n else 'catalog missing'); self.pill.setStyleSheet('' if n else f"color:{C['ko']}")
        self.zoomL.setText(f'{self.view.zoom_percent()} %'); self.cntL.setText(tr('{0} nodes · {1} links', len(self.graph.nodes), len(self.graph.edges)))

    def build_state(self, running):
        self._building = running; self.bBuild.setText(' Stop' if running else ' Compile'); self.bBuild.setIcon(icon('stop_fill' if running else 'play_fill', '#ffffff', 16))

    def fold_icon(self): self.bFold.setIcon(icon('up' if getattr(self, 'out_collapsed', False) else 'down', size=16))

    def toggle_output(self, collapse=None):
        collapse = (not self.out_collapsed) if collapse is None else collapse
        if collapse == self.out_collapsed: return
        if collapse:
            self.out_h = self.dock_out.height(); self.stack.hide()
            h = max(self.tabs.tabBar().sizeHint().height(), self.tabs.cornerWidget().sizeHint().height()) + 10; self.dock_out.setMinimumHeight(h); self.dock_out.setMaximumHeight(h)
        else:
            self.stack.show(); self.dock_out.setMinimumHeight(0); self.dock_out.setMaximumHeight(BIG); self.resizeDocks([self.dock_out], [max(self.out_h, 220)], Qt.Vertical)
        self.out_collapsed = collapse; self.fold_icon()

    def refresh_code(self):
        try: txt, self.hl_map = self.graph.gen_map()
        except Exception as e: txt, self.hl_map = f'// Generation error: {e}', {}
        sb = self.code.verticalScrollBar(); v = sb.value(); self.code.setPlainText(txt); sb.setValue(v); self.highlight(self.insp.nid, False)
        self.probs.clear()
        for lvl, nid, msg in self.graph.problems():
            col = {'err': C['ko'], 'warn': '#e6a23c'}.get(lvl, '#4f8cf0'); it = QListWidgetItem(icon({'err': 'error', 'warn': 'warn'}.get(lvl, 'info'), col, 16), msg); it.setData(Qt.UserRole, nid); self.probs.addItem(it)
        self.tabs.setTabText(2, tr('Problems ({0})', self.probs.count()) if self.probs.count() else 'Problems')

    def on_changed(self):
        self.refresh_code(); self.snap_t.start()
        if self.insp.nid and self.insp.nid not in self.graph.nodes: self.insp.show_node(0)
        else: self.insp.refresh()

    def field_changed(self): self.scene.rebuild(keep=[self.insp.nid]); self.on_changed()
    def value_changed(self): self.scene.rebuild(keep=[self.insp.nid]); self.refresh_code(); self.snap_t.start()
    def includes_changed(self): self.graph.inc = self.incs.toPlainText(); self.refresh_code(); self.snap_t.start()

    def snapshot(self):
        s = self.graph.to_json(); self.update_title()
        if self.hi >= 0 and self.hist[self.hi] == s: return
        self.hist = (self.hist[:self.hi + 1] + [s])[-80:]; self.hi = len(self.hist) - 1
        if self.cfg.get('pref_autosave', True):
            try: GRAPHF.write_text(s, 'utf-8')
            except Exception: pass

    def hist_go(self, d):
        self.snapshot(); i = self.hi + d
        if 0 <= i < len(self.hist): self.hi = i; self.load_state(self.hist[i])
        self.update_title()

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

    def add_plugin_function(self, pos=None, plugin=''):
        """Plugin function browser (catalogs of the enabled plugins); every function chosen becomes a node."""
        if not PN.CATALOG:
            if QMessageBox.question(self, 'Plugin functions', 'No enabled plugin offers a function catalog.\n\nThe "Dear ImGui" plugin is one: it is disabled by default. Open the Plugin explorer to enable it?') == QMessageBox.Yes: self.open_plugins()
            return
        self._plugfn_nodes = []; dlg = PluginFunctionDialog(self, plugin); dlg.chosen.connect(lambda pid: self._place_plugin_fn(pid, pos)); dlg.exec()
        return self._plugfn_nodes[0] if self._plugfn_nodes else None

    def _place_plugin_fn(self, pid, pos):
        d = PN.catalog_def(pid)
        if d:
            n = self._place('plug', PN.defaults(d), pos); getattr(self, '_plugfn_nodes', []).append(n)

    def fill_template_menu(self):
        """File > New from template: the templates of the enabled plugins."""
        self.tplMenu.clear(); n = 0
        for pl in MANAGER.plugins:
            if not pl.enabled: continue
            for name, path, desc in pl.templates:
                a = self.tplMenu.addAction(f'{name}  ({pl.title})', lambda _=False, p=path: self.new_from_template(p)); a.setToolTip(desc); a.setStatusTip(desc); n += 1
        if not n: self.tplMenu.addAction('(no template: enable a plugin that has some, like Dear ImGui)').setEnabled(False)

    def new_from_template(self, path):
        if (self.graph.nodes or self.graph.notes) and QMessageBox.question(self, 'New from template', 'Replace the current graph with this template?\n(Ctrl+Z brings your graph back.)') != QMessageBox.Yes: return
        try: self.load_state(Path(path).read_text('utf-8'))
        except Exception as e: QMessageBox.critical(self, 'Template', tr('Cannot load the template:\n{0}', e)); return
        self.file = None; self.saved_json = None; self.snapshot(); self.view.fit(); self.statusBar().showMessage('Template loaded: use Write to project (Ctrl+E) or Compile (F5)', 6000)
        for pl in MANAGER.plugins:
            if pl.enabled and pl.base and any(Path(path) == t[1] for t in pl.templates): BD.offer(self, pl, 'This template uses it.')

    def offer_base(self, pl):
        return BD.offer(self, pl, tr('"{0}" is now enabled.', pl.title))

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
        if PN.CATALOG: m.addAction('Plugin function…', lambda: self._drop_make(nid, pid, d, pos, '@plugfn'))
        for cat in CATEGORIES:
            if cat in cats:
                sm = m.addMenu(cat)
                for name in cats[cat]: sm.addAction(name, lambda _=False, name=name: self._drop_make(nid, pid, d, pos, name))
        m.exec(screen)

    def _drop_make(self, nid, pid, d, pos, name):
        g = self.graph; src = g.pin_type(nid, pid, d); where = pos if d == 'o' else QPointF(pos.x() - 220, pos.y())
        n = self.browse(where) if name is None else self.add_plugin_function(where) if name == '@plugfn' else self.add_pre(name, where)
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
        m = QMenu(self); m.addAction('Game function…' + self.sk(self.aBrowse), lambda: self.browse(pos))
        if PN.CATALOG: m.addAction('Plugin function…' + self.sk(self.aPlugFn), lambda: self.add_plugin_function(pos))
        m.addAction('Find in the graph…' + self.sk(self.aFind), lambda: self.find()); m.addAction('Comment here…', lambda: self.add_note(pos))
        if self.scene.selected_ids(): m.addAction('Group selected nodes' + self.sk(self.aGroup), self.group_selected)
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
        if not self.confirm_discard(): return
        if self.cfg.get('pref_confirm_new', True) and QMessageBox.question(self, 'New graph', 'Clear the current graph?' + ('\n\nYour startup graph will be loaded.' if STARTF.exists() else '')) != QMessageBox.Yes: return
        self.graph.clear(); self.graph.inc = DEFAULT_INC; self.file = None; self.saved_json = None  # includes go back to the standard list (a startup graph brings its own)
        if self.cfg.get('pref_new', 'startup') == 'startup' and STARTF.exists():
            try: self.graph.load_json(STARTF.read_text('utf-8'))
            except Exception: self.graph.clear()  # unreadable startup graph: an empty one
        self.incs.blockSignals(True); self.incs.setPlainText(self.graph.inc); self.incs.blockSignals(False)
        self.scene.rebuild(keep=[]); self.insp.show_node(0); self.refresh_code(); self.snapshot(); self.view.fit()

    def clear_graph(self):
        """Remove every node, link, group and comment (the file name and the includes list are kept)."""
        if not self.graph.nodes and not self.graph.groups and not self.graph.notes: self.statusBar().showMessage('The graph is already empty', 3000); return
        if QMessageBox.question(self, 'Clear the graph', tr('Remove all {0} nodes, the links, groups and comments?\n(Ctrl+Z brings them back.)', len(self.graph.nodes))) != QMessageBox.Yes: return
        inc = self.graph.inc; self.graph.clear(); self.graph.inc = inc
        self.scene.rebuild(keep=[]); self.insp.show_node(0); self.scene.changed.emit(); self.statusBar().showMessage('Graph cleared', 3000)

    def open(self):
        if not self.confirm_discard(): return
        start = str(Path(self.file).parent) if self.file else ''
        p, _ = QFileDialog.getOpenFileName(self, 'Open a graph', start, FILTER_OPEN)
        if p: self.open_path(p)

    def open_path(self, p):
        """Open a graph file; it becomes the current file (Ctrl+S saves back into it)."""
        try: txt = Path(p).read_text('utf-8'); self.load_state(txt)
        except Exception as e: QMessageBox.critical(self, 'Cannot open file', str(e)); return False
        self.file = str(p); self.saved_json = self.graph.to_json(); self.remember(self.file); self.snapshot(); self.view.fit(); self.statusBar().showMessage(tr('Opened: {0}', p), 4000); return True

    def save(self):
        """Ctrl+S: write into the current file; ask for a name only when there is none (or it is an old .json)."""
        if not self.file or Path(self.file).suffix.lower() != '.odn': return self.save_as()
        return self.write_graph(self.file)

    def save_as(self):
        start = str(Path(self.file).with_suffix('.odn')) if self.file else 'my_mod.odn'
        p, _ = QFileDialog.getSaveFileName(self, 'Save the graph', start, FILTER_SAVE)
        if not p: return False
        return self.write_graph(str(Path(p).with_suffix('.odn')))  # graphs are always saved as .odn (.json is only read, for older files)

    def write_graph(self, p):
        txt = self.graph.to_json()
        try:
            tmp = Path(p + '.tmp'); tmp.write_text(txt, 'utf-8'); os.replace(tmp, p)  # a crash while writing never leaves a half file
        except Exception as e: QMessageBox.critical(self, 'Cannot save', f'{p}\n\n{e}'); return False
        self.file = p; self.saved_json = txt; self.remember(p); self.update_title(); self.statusBar().showMessage(tr('Saved: {0}', p), 4000); return True

    # ---- current file, unsaved changes, recent files ----
    def dirty(self):
        if self.file: return self.graph.to_json() != getattr(self, 'saved_json', None)
        return False   # an untitled graph is kept by the session autosave; nothing to ask about

    def update_title(self):
        name = Path(self.file).name if self.file else 'Untitled'
        self.setWindowTitle(tr('{0}{1} - Odyssey Node Editor v{2}', name, ' •' if self.dirty() else '', __version__)); self.setWindowModified(False)
        if self.file: self.cfg['last_file'] = self.file

    def confirm_discard(self):
        """True when it is fine to replace / close the current graph: nothing unsaved, or the person chose Save / Discard."""
        if not self.dirty(): return True
        box = QMessageBox(QMessageBox.Question, 'Unsaved changes', tr('Save the changes to {0}?', Path(self.file).name), QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, self); box.setDefaultButton(QMessageBox.Save)
        r = box.exec()
        if r == QMessageBox.Save: return bool(self.save())
        return r == QMessageBox.Discard

    def remember(self, p):
        rec = [x for x in self.cfg.get('recent', []) if x != p]; self.cfg['recent'] = ([str(p)] + rec)[:10]; save_config(self.cfg)

    def fill_recent_menu(self):
        m = self.recentMenu; m.clear(); rec = self.cfg.get('recent', [])
        for i, p in enumerate(rec):
            a = m.addAction(f'&{i + 1 if i < 9 else 0}  {Path(p).name}', lambda _=False, p=p: self.open_recent(p)); a.setToolTip(p); a.setStatusTip(p)
        if not rec: m.addAction('(no recent file)').setEnabled(False)
        else: m.addSeparator(); m.addAction('Clear the list', lambda: (self.cfg.__setitem__('recent', []), save_config(self.cfg)))

    def open_recent(self, p):
        if not Path(p).is_file():
            QMessageBox.information(self, 'Open recent', tr('This file no longer exists:\n{0}', p)); self.cfg['recent'] = [x for x in self.cfg.get('recent', []) if x != p]; save_config(self.cfg); return
        if self.confirm_discard(): self.open_path(p)

    def save_cpp(self):
        p, _ = QFileDialog.getSaveFileName(self, 'Save the code', 'main.cpp', 'C++ (*.cpp *.hpp *.h)')
        if p:
            with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(self.code.toPlainText())

    def write_project(self):
        p = main_cpp_path(self.cfg)
        if not p: QMessageBox.information(self, 'Write to project', 'Set your exlaunch project in Settings first.'); self.configure(); return False
        if Path(p).suffix.lower() not in ('.cpp', '.hpp', '.h'): QMessageBox.warning(self, 'Write to project', 'The generated file must end in .cpp, .hpp or .h.'); return False
        if not Path(p).parent.is_dir(): QMessageBox.warning(self, 'Write to project', tr('Folder not found: {0}', Path(p).parent)); return False
        BD.check_graph(self, self.graph); txt = self.code.toPlainText()
        with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(txt)
        self.statusBar().showMessage(tr('Written: {0} ({1} bytes)', p, len(txt.encode())), 5000); return True

    # ---------- build ----------
    def build(self):
        if self.runner.running(): self.runner.stop(); return
        if not self.cfg['build_cmd']: QMessageBox.information(self, 'Compile', 'The build command is empty: see Settings.'); self.configure(); return
        if not self.cfg.get('build_env') and not self.ask_env(): return
        env, cwd = self.cfg['build_env'], self.cfg['project_dir'] or None
        if cwd and not (env == 'wsl' and cwd.startswith('/')) and not Path(cwd).is_dir(): QMessageBox.warning(self, 'Compile', tr('Project folder not found: {0}', cwd)); return
        self.suggest_build_cmd()
        errs = [m for lvl, _, m in self.graph.problems() if lvl == 'err']
        if errs and QMessageBox.question(self, 'Compile', tr('The graph has {0} error(s), for example:\n\n• ', len(errs)) + '\n• '.join(errs[:3]) + '\n\nCompile anyway?') != QMessageBox.Yes: self.tabs.setCurrentWidget(self.probs); return
        self.toggle_output(False); self.tabs.setCurrentWidget(self.log); self.log.clear()
        self.log.appendPlainText('Step 1/2: write the generated code into the project')
        if not self.write_project(): self.log.appendPlainText('  could not write the file: nothing was compiled.'); return
        p = main_cpp_path(self.cfg); self.log.appendPlainText(tr('  {0}  ({1} lines)', p, len(self.code.toPlainText().splitlines())))
        where = f'{env}{" · " + self.cfg.get("wsl_distro", "") if env == "wsl" and self.cfg.get("wsl_distro") else ""}'
        self.log.appendPlainText(tr('Step 2/2: build   [{0}]  in {1}\n$ {2}\n', where, cwd or '(current folder)', self.cfg['build_cmd'])); self.t0 = time.monotonic()
        self.build_state(True); self.bst.setText('Build running…'); self.bst.setStyleSheet(''); self.runner.start(self.cfg['build_cmd'], cwd, env, self.cfg.get('wsl_distro', ''))

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
            self.statusBar().showMessage(tr('Log saved: {0}', p), 5000)

    def copy_log(self, errors_only):
        t = self.log.toPlainText()
        if errors_only:
            keys = re.compile(r'error|\bfailed\b|\*\*\*|undefined reference|fatal|warning|cannot|no such file|not found|<3>', re.I)
            t = '\n'.join(l for l in t.splitlines() if keys.search(l)) or '(no error lines found)'
        QGuiApplication.clipboard().setText(t); self.statusBar().showMessage(tr('Copied the error lines ({0} characters)', len(t)) if errors_only else tr('Copied the console ({0} characters)', len(t)), 4000)

    def repair_base(self):
        """Delete <project>/build, then re-run cmake with the exlaunch toolchain."""
        if self.runner.running(): QMessageBox.information(self, 'Repair', 'A command is already running: stop it first.'); return
        if not self.cfg['project_dir']: QMessageBox.information(self, 'Repair', 'Set the exlaunch project folder in Settings first.'); self.configure(); return
        if not self.cfg.get('build_env') and not self.ask_env(): return
        env, cwd = self.cfg['build_env'], self.cfg['project_dir']
        if not (env == 'wsl' and cwd.startswith('/')) and not Path(cwd).is_dir(): QMessageBox.warning(self, 'Repair', tr('Project folder not found: {0}', cwd)); return
        if QMessageBox.question(self, 'Repair exlaunch base', tr('This DELETES the "build" folder of:\n{0}\n\nand runs:\ncmake -B build -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain.cmake\n\nContinue?', cwd)) != QMessageBox.Yes: return
        cm = 'cmake -B build -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain.cmake'
        cmd = f'(if exist build rmdir /s /q build) & {cm}' if env == 'windows' or (env == '' and os.name == 'nt') else f'rm -rf build && {cm}'
        self.toggle_output(False); self.tabs.setCurrentWidget(self.log); self.log.clear(); self.log.appendPlainText(tr('[repair · {0}] $ {1}\n', env, cmd))
        self.build_state(True); self.bst.setText('Repair running…'); self.bst.setStyleSheet(''); self.runner.start(cmd, cwd, env, self.cfg.get('wsl_distro', ''))

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
        self.build_state(False); ok = code == 0; self.bst.setText('Build succeeded' if ok else tr('Build failed (code {0})', code)); self.bst.setStyleSheet(f'color:{"#4ecb8a" if ok else "#ef5b5b"}')
        el = time.monotonic() - getattr(self, 't0', time.monotonic()); errs = [l.strip() for l in self.log.toPlainText().splitlines() if re.search(r'\berror\b|undefined reference|\*\*\*', l)]
        if not ok and errs: self.bst.setText(tr('Build failed ({0} error line(s))', len(errs)))
        self.log.appendPlainText(f'\n{"Build succeeded" if ok else "Build failed (code " + str(code) + ")"} in {el:.1f}s')
        if not ok and errs: self.log.appendPlainText('Main errors:\n  ' + '\n  '.join(l[-200:] for l in errs[:5]) + '\n(use "Copy errors" to copy every error line)')
        elif ok: self.log.appendPlainText('Next step: Ryujinx tab > "Install mod and launch".')
        self.statusBar().showMessage(self.bst.text(), 6000)
        cb, self.after_build = self.after_build, None
        if cb and ok: cb()
        elif cb: self.ryu.say('Build failed: the game was not started.')
        self.ryu.refresh()

    # ---------- preferences ----------
    def set_look(self, mode=None, accent=None):
        if mode: self.cfg['pref_theme'] = mode
        if accent: self.cfg['pref_accent'] = accent
        save_config(self.cfg); self.apply_prefs()

    def sync_look_menu(self):
        if hasattr(self, 'lookActs'):
            cur = self.cfg.get('pref_theme', 'dark'); (self.lookActs.get(cur) or self.lookActs['dark']).setChecked(True); (self.accentActs.get(self.cfg.get('pref_accent', 'Red')) or self.accentActs['Red']).setChecked(True)
            for nm, a in self.accentActs.items(): pm = QPixmap(14, 14); pm.fill(QColor(self.theme_accent(nm))); a.setIcon(QIcon(pm))

    def apply_prefs(self):
        c = self.cfg; qss = 'QPlainTextEdit{font-size:%dpt}' % int(c['pref_code_size'])
        self.code.setStyleSheet(qss); self.incs.setStyleSheet(qss); self.log.setStyleSheet(qss)
        self.code.setLineWrapMode(QPlainTextEdit.WidgetWidth if c['pref_wrap'] else QPlainTextEdit.NoWrap)
        inst, cst = self.graph.install, self.graph.calls; self.graph.install, self.graph.calls = c.get('pref_install', 'symbol'), c.get('pref_calls', 'direct'); self.scene.autogroup = bool(c.get('pref_autogroup', True)); self.scene.dropmenu = bool(c.get('pref_dropmenu', True)); self.code.set_numbers(c.get('pref_linenumbers', True)); self.scene.links_top = bool(c.get('pref_links_top')); self.scene.apply_z(); self.view.show_grid = bool(c['pref_grid']); self.view.viewport().update(); self.scene.snap = bool(c['pref_snap'])
        look = (c.get('pref_theme', 'dark'), c.get('pref_accent', 'Red'))
        if getattr(self, '_ui_px', None) != int(c['pref_ui_size']) or getattr(self, '_look', None) != look:
            changed = getattr(self, '_look', look) != look; self._ui_px = int(c['pref_ui_size']); self._look = look; set_theme(*look); apply_theme(QApplication.instance(), self._ui_px)
            if hasattr(self, 'fbar'):  # the theme changed on a running window: icons, code colors, search bar, canvas
                icons.refresh(); self.build_state(getattr(self, '_building', False)); self.fold_icon(); self.hlt.restyle(); self.fbar.restyle(); self.scene.update(); self.view.viewport().update(); self.refresh_code(); self.sync_look_menu()
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
        had = STARTF.exists(); n = len(self.graph.nodes)
        if QMessageBox.question(self, 'Startup graph', tr_n('Replace your startup graph with the current graph ({0} node)?\n\nFile > New and the startup option will open it.', 'Replace your startup graph with the current graph ({0} nodes)?\n\nFile > New and the startup option will open it.', n) if had else tr_n('Use the current graph as your startup graph ({0} node)?\n\nFile > New and the startup option will open it.', 'Use the current graph as your startup graph ({0} nodes)?\n\nFile > New and the startup option will open it.', n)) != QMessageBox.Yes: return
        try: STARTF.write_text(self.graph.to_json(), 'utf-8'); self.statusBar().showMessage('Saved as your startup graph: File > New and the startup option now use it', 6000)
        except Exception as e: QMessageBox.critical(self, 'Startup graph', str(e))

    def clear_startup(self):
        if not STARTF.exists(): self.statusBar().showMessage('There is no startup graph', 4000); return
        if QMessageBox.question(self, 'Startup graph', 'Forget your startup graph?\n\nFile > New will show the example again.') != QMessageBox.Yes: return
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
        if c is bR: self.load_state(g2.to_json()); self.file = None; self.saved_json = None; self.snapshot(); self.view.fit()
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
        what = 'Saves this function with everything it uses (its blocks, values, called functions, globals).' if expand else tr('Saves the {0} selected node(s) as a template.', len(sel))
        name, ok = QInputDialog.getText(self, 'Save to library', what + '\nName:', text=default)
        if not ok or not name.strip(): return
        if (library.LIBDIR / (library.safe_name(name) + library.EXT)).exists() and QMessageBox.question(self, 'Library', tr('"{0}" already exists. Replace it?', name)) != QMessageBox.Yes: return
        p = library.save(self.graph, sel, name.strip(), expand=expand); self.pal.set_library(library.entries()); self.statusBar().showMessage(tr('Saved to your library: {0}', p), 6000)

    def open_library(self):
        d = LibraryDialog(self); d.insert_requested.connect(lambda p: self.insert_lib(p, None)); d.exec(); self.pal.set_library(library.entries())

    def fill_lib_menu(self):
        self.libMenu.clear(); es = library.entries()
        for p, name, desc, n in es: self.libMenu.addAction(f'{name}  ({n})', lambda _=False, p=str(p): self.insert_lib(p, None))
        if not es: self.libMenu.addAction('(empty)').setEnabled(False)

    def insert_lib(self, path, pos):
        try: frag = library.load(path)
        except Exception as e: QMessageBox.critical(self, 'Library', tr('Cannot read {0}: {1}', path, e)); return
        pos = pos or self.center(); new, notes = library.insert(self.graph, frag, pos.x(), pos.y()); self.scene.commit(keep=new)
        self.statusBar().showMessage(tr('Inserted {0}', frag.get('name', '')) + (' - ' + '; '.join(notes) if notes else ''), 7000)

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
        QMessageBox.about(self, 'Odyssey Node Editor', tr('<h3>Made by WibiDev</h3><b>Odyssey Node Editor</b> v{0}: a node editor that generates exlaunch C++ (Super Mario Odyssey 1.0.0).<br><br>Credits: OdysseyDecomp (MonsterDruide1 and contributors), exlaunch (shadowninja108), sead and nnheaders (open-ead), SMO-Exlaunch-Base (CraftyBoss) and LunaKit (Amethyst-szs) for the Dear ImGui plugin, Dear ImGui (Omar Cornut), Qt for Python (PySide6), icons drawn after the Lucide style. Inspired by Unreal Engine Blueprints.<br>Unofficial mod tool, not affiliated with Nintendo.', __version__))

    def closeEvent(self, ev):
        if not self.confirm_discard(): ev.ignore(); return
        self.snapshot(); save_config(self.cfg); self.runner.stop(); s = QSettings('OdysseyNodes', 'OdysseyNodes'); s.setValue('geom', self.saveGeometry()); s.setValue('state', self.saveState()); super().closeEvent(ev)
