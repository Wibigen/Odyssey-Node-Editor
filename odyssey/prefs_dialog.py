"""Preferences: how the editor behaves and looks (the project / build settings are in Settings)."""
from PySide6.QtGui import QColor, QIcon, QPixmap
from .icons import icon
from .theme import ACCENTS, PLUGIN_THEMES, theme_choices
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSpinBox, QTabWidget, QVBoxLayout, QWidget)

from .config import DEFAULTS
from .graph import CALL_STYLES

NEWMODE = [('startup', 'My startup graph (empty if none saved)'), ('empty', 'Nothing: an empty graph')]
STARTUP = [('session', 'Reopen where I left off (last session)'), ('startup', 'My startup graph (File > Save as startup graph)'), ('example', 'The example graph'), ('empty', 'An empty graph')]


class PrefsDialog(QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent); self.cfg = cfg; self.setWindowTitle('Preferences'); self.setMinimumWidth(520); top = QVBoxLayout(self); tabs = QTabWidget(); top.addWidget(tabs); gen, adv = QWidget(), QWidget(); tabs.addTab(gen, 'General'); tabs.addTab(adv, 'Advanced'); v = QVBoxLayout(gen)
        g = QGroupBox('Startup and files'); f = QFormLayout(g)
        self.startup = QComboBox()
        for k, lab in STARTUP: self.startup.addItem(lab, k)
        self.startup.setToolTip('What you see when the program starts. File > New also uses your startup graph when you saved one.')
        self.autosave = QCheckBox('Save the current graph automatically (restores it after a crash)'); self.confirm = QCheckBox('Ask before File > New clears the graph')
        self.newmode = QComboBox()
        for k, lab in NEWMODE: self.newmode.addItem(lab, k)
        self.newmode.setToolTip('What File > New shows. The startup graph is saved with File > Save as startup graph.')
        f.addRow('Open on', self.startup); f.addRow('File > New shows', self.newmode); f.addRow(self.autosave); f.addRow(self.confirm); v.addWidget(g)
        g = QGroupBox('Appearance'); f = QFormLayout(g)
        self.theme = QComboBox()
        for key, lab, base in theme_choices(): self.theme.addItem(icon('moon' if base == 'dark' else 'sun', size=16), lab, key)
        self.accent = QComboBox(); self.accent.addItem('Theme default', 'Theme')
        for nm, col in ACCENTS.items(): pm = QPixmap(14, 14); pm.fill(QColor(col)); self.accent.addItem(QIcon(pm), nm, nm)
        f.addRow('Theme', self.theme); f.addRow('Accent color', self.accent); v.addWidget(g)
        g = QGroupBox('Canvas'); f = QFormLayout(g)
        self.linktop = QCheckBox('Draw the links of the selected node above everything else'); self.linktop.setToolTip('Select a node: its links are drawn on top of the other nodes so you can follow them.')
        self.autogroup = QCheckBox('Put a node into a group when I drop it inside the group frame'); self.autogroup.setToolTip('Only nodes that are not in a group yet. You can also right-click a node in front of a group.')
        self.dropmenu = QCheckBox('Open the add-a-block menu when I release a link on empty space'); self.dropmenu.setToolTip('Drag a link from a pin and let go on empty canvas: choose a block and it is created and connected.')
        self.grid = QCheckBox('Show the dotted grid'); self.snap = QCheckBox('Snap nodes to the grid while dragging')
        f.addRow(self.grid); f.addRow(self.snap); f.addRow(self.linktop); f.addRow(self.autogroup); f.addRow(self.dropmenu); v.addWidget(g)
        g = QGroupBox('Code preview'); f = QFormLayout(g)
        self.hl = QCheckBox('Highlight the lines of the selected node'); self.hl.setToolTip('Select a node and the C++ lines it produces are highlighted and scrolled into view.')
        self.lnum = QCheckBox('Show line numbers'); self.wrap = QCheckBox('Wrap long lines'); self.csize = QSpinBox(); self.csize.setRange(7, 24); self.csize.setSuffix(' pt')
        f.addRow(self.hl); f.addRow(self.lnum); f.addRow(self.wrap); f.addRow('Code font size', self.csize); v.addWidget(g)
        g = QGroupBox('Interface'); f = QFormLayout(g)
        self.ui = QSpinBox(); self.ui.setRange(10, 20); self.ui.setSuffix(' px'); f.addRow('Text size', self.ui); v.addWidget(g)
        v.addStretch(1); va = QVBoxLayout(adv); g = QGroupBox('Generated code'); f = QFormLayout(g)
        self.install = QComboBox(); self.install.addItem('By symbol: Hook::InstallAtSymbol("_ZN...")  (recommended)', 'symbol'); self.install.addItem('By offset: Hook::InstallAtOffset(0x...)', 'offset')
        self.install.setToolTip('How hooks are installed. A symbol keeps working when the offset changes; the offset form is the fallback and is used automatically for a hook whose symbol is unknown.')
        self.calls = QComboBox()
        for k, lab in CALL_STYLES: self.calls.addItem(lab, k)
        self.calls.setToolTip('How a game function is called. Direct needs the decomp headers (included) and the symbols linked by your base project. A single block can override this (Call style in the inspector).')
        f.addRow('Call game functions', self.calls); f.addRow('Install hooks', self.install); va.addWidget(g); va.addStretch(1)
        row = QHBoxLayout(); b = QPushButton('Restore defaults'); b.clicked.connect(self.defaults); row.addWidget(b); row.addStretch(1)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); row.addWidget(bb); top.addLayout(row)
        note = QLabel('Project folder, build command and the function catalog are in Tools > Settings.'); note.setStyleSheet('color:#8a91a5'); note.setWordWrap(True); top.addWidget(note)
        self.load(cfg)

    def load(self, c):
        self.startup.setCurrentIndex(max(0, self.startup.findData(c['pref_startup']))); self.autosave.setChecked(bool(c['pref_autosave'])); self.confirm.setChecked(bool(c['pref_confirm_new']))
        self.theme.setCurrentIndex(max(0, self.theme.findData(c.get('pref_theme', 'dark')))); self.accent.setCurrentIndex(max(0, self.accent.findData(c.get('pref_accent', 'Red')))); self.autogroup.setChecked(bool(c.get('pref_autogroup', True))); self.dropmenu.setChecked(bool(c.get('pref_dropmenu', True))); self.lnum.setChecked(bool(c.get('pref_linenumbers', True))); self.calls.setCurrentIndex(max(0, self.calls.findData(c.get('pref_calls', 'direct')))); self.newmode.setCurrentIndex(max(0, self.newmode.findData(c.get('pref_new', 'startup')))); self.linktop.setChecked(bool(c.get('pref_links_top'))); self.grid.setChecked(bool(c['pref_grid'])); self.snap.setChecked(bool(c['pref_snap'])); self.hl.setChecked(bool(c['pref_highlight']))
        self.install.setCurrentIndex(max(0, self.install.findData(c.get('pref_install', 'symbol')))); self.wrap.setChecked(bool(c['pref_wrap'])); self.csize.setValue(int(c['pref_code_size'])); self.ui.setValue(int(c['pref_ui_size']))

    def defaults(self): self.load({k: v for k, v in DEFAULTS.items() if k.startswith('pref_')})

    def values(self):
        return dict(pref_startup=self.startup.currentData(), pref_autosave=self.autosave.isChecked(), pref_confirm_new=self.confirm.isChecked(), pref_grid=self.grid.isChecked(),
                    pref_snap=self.snap.isChecked(), pref_highlight=self.hl.isChecked(), pref_wrap=self.wrap.isChecked(), pref_code_size=self.csize.value(), pref_ui_size=self.ui.value(), pref_install=self.install.currentData(), pref_theme=self.theme.currentData(), pref_accent=self.accent.currentData(), pref_autogroup=self.autogroup.isChecked(), pref_dropmenu=self.dropmenu.isChecked(), pref_linenumbers=self.lnum.isChecked(), pref_calls=self.calls.currentData(), pref_new=self.newmode.currentData(), pref_links_top=self.linktop.isChecked())
