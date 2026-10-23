"""Plugin explorer: every installed plugin with its picture, author, version and description; enable, disable, install, remove, create."""
import hashlib
from pathlib import Path

from PySide6.QtCore import QSize, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QIcon, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import (QDialog, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox, QPlainTextEdit,
                               QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QDialogButtonBox)

from . import plugnodes as PN
from .icons import bind, icon
from .plugins import MANAGER, USER_DIR
from . import basepatch_dialog as BD
from .basepatch import BasePatch
from .theme import C

PALETTE = ('#3a7bd5', '#2fa66a', '#c98a2b', '#9a66e8', '#e8484f', '#14a3a3', '#e0609e', '#7a7f90')


def plugin_pixmap(pl, size=64):
    """The plugin picture as a square (cropped from the middle when it is not square); a letter on a colored square when the plugin has none."""
    dpr = 2.0; px = int(size * dpr); pm = QPixmap(str(pl.image)) if pl.image else QPixmap()
    out = QPixmap(px, px); out.fill(Qt.transparent); p = QPainter(out); p.setRenderHint(QPainter.Antialiasing); p.setRenderHint(QPainter.SmoothPixmapTransform)
    r = px * 0.18
    if not pm.isNull():
        from PySide6.QtGui import QPainterPath
        side = min(pm.width(), pm.height()); pm = pm.copy((pm.width() - side) // 2, (pm.height() - side) // 2, side, side).scaled(px, px, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        path = QPainterPath(); path.addRoundedRect(0, 0, px, px, r, r); p.setClipPath(path); p.drawPixmap(0, 0, pm)
    else:
        col = QColor(pl.color if pl.color.startswith('#') else PALETTE[int(hashlib.md5(pl.id.encode()).hexdigest(), 16) % len(PALETTE)])
        g = QLinearGradient(0, 0, px, px); g.setColorAt(0, col.lighter(115)); g.setColorAt(1, col.darker(120)); p.setBrush(g); p.setPen(Qt.NoPen); p.drawRoundedRect(0, 0, px, px, r, r)
        f = QFont(); f.setBold(True); f.setPixelSize(int(px * 0.5)); p.setFont(f); p.setPen(QColor('#ffffff')); p.drawText(0, 0, px, px, Qt.AlignCenter, (pl.title or '?')[:1].upper())
    p.end(); out.setDevicePixelRatio(dpr); return out


class NewPluginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle('New plugin'); self.setMinimumWidth(440); v = QVBoxLayout(self); f = QFormLayout()
        self.title, self.author, self.desc = QLineEdit('My plugin'), QLineEdit(), QLineEdit(); f.addRow('Title', self.title); f.addRow('Author', self.author); f.addRow('Description', self.desc); v.addLayout(f)
        n = QLabel('A folder with a ready-to-edit plugin.json (one example node and one example theme) is created in your plugins folder. See PLUGINS.md for the format.'); n.setWordWrap(True); n.setStyleSheet(f"color:{C['mu']}"); v.addWidget(n)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); v.addWidget(bb)


class PluginExplorer(QDialog):
    changed = Signal()   # emitted after anything that changes what is loaded (the window reloads and refreshes)

    def __init__(self, cfg, reload, parent=None):
        super().__init__(parent); self.cfg, self.reload = cfg, reload; self.setWindowTitle('Plugin explorer'); self.resize(960, 600); self.setMinimumSize(760, 480)
        top = QVBoxLayout(self); sp = QSplitter(); top.addWidget(sp, 1)
        left = QWidget(); lv = QVBoxLayout(left); lv.setContentsMargins(0, 0, 0, 0)
        self.q = QLineEdit(); self.q.setPlaceholderText('Search plugins…'); self.q.setClearButtonEnabled(True); self.q.textChanged.connect(self.fill); lv.addWidget(self.q)
        self.lst = QListWidget(); self.lst.setIconSize(QSize(44, 44)); self.lst.setSpacing(2); self.lst.currentRowChanged.connect(self.show_plugin); lv.addWidget(self.lst, 1); sp.addWidget(left)
        right = QWidget(); rv = QVBoxLayout(right); rv.setContentsMargins(12, 0, 0, 0); head = QHBoxLayout(); self.pic = QLabel(); self.pic.setFixedSize(96, 96); head.addWidget(self.pic)
        hv = QVBoxLayout(); self.name = QLabel(); self.name.setStyleSheet('font-size:20px;font-weight:600'); self.by = QLabel(); self.badges = QLabel(); self.badges.setTextFormat(Qt.RichText)
        hv.addWidget(self.name); hv.addWidget(self.by); hv.addWidget(self.badges); hv.addStretch(1); head.addLayout(hv, 1); rv.addLayout(head)
        self.desc = QLabel(); self.desc.setWordWrap(True); self.desc.setTextInteractionFlags(Qt.TextSelectableByMouse); rv.addWidget(self.desc)
        self.sum = QLabel(); self.sum.setStyleSheet(f"color:{C['mu']}"); rv.addWidget(self.sum)
        self.tree = QTreeWidget(); self.tree.setHeaderHidden(True); rv.addWidget(self.tree, 1)
        self.err = QPlainTextEdit(); self.err.setReadOnly(True); self.err.setMaximumHeight(70); self.err.setStyleSheet(f"color:{C['ko']}"); rv.addWidget(self.err)
        row = QHBoxLayout(); self.bToggle, self.bRemove, self.bOpen = QPushButton('Disable'), QPushButton('Remove'), QPushButton('Show folder'); self.bBase, self.bFuncs = QPushButton('Exlaunch base…'), QPushButton('Function browser…')
        bind(self.bRemove, 'trash', size=16); bind(self.bOpen, 'open', size=16); bind(self.bBase, 'wrench', size=16); bind(self.bFuncs, 'func', size=16)
        for b in (self.bToggle, self.bFuncs, self.bBase, self.bRemove, self.bOpen): row.addWidget(b)
        row.addStretch(1); rv.addLayout(row); sp.addWidget(right); sp.setStretchFactor(1, 1); sp.setSizes([330, 630])
        bot = QHBoxLayout(); self.bInstall, self.bNew, self.bReload, self.bFolder = QPushButton('Install…'), QPushButton('New plugin…'), QPushButton('Reload'), QPushButton('Plugins folder')
        bind(self.bInstall, 'plus', size=16); bind(self.bNew, 'note', size=16); bind(self.bFolder, 'open', size=16)
        m = QMenu(self); m.addAction('From an archive (.zip / .odnp)…', self.install_file); m.addAction('From a folder…', self.install_dir); self.bInstall.setMenu(m)
        for b in (self.bInstall, self.bNew, self.bReload, self.bFolder): bot.addWidget(b)
        bot.addStretch(1); close = QPushButton('Close'); close.clicked.connect(self.accept); bot.addWidget(close); top.addLayout(bot)
        self.bBase.clicked.connect(self.base_dialog); self.bFuncs.clicked.connect(self.open_funcs); self.bToggle.clicked.connect(self.toggle); self.bRemove.clicked.connect(self.remove); self.bOpen.clicked.connect(lambda: self.open_dir(self.cur().path if self.cur() else USER_DIR))
        self.bNew.clicked.connect(self.new_plugin); self.bReload.clicked.connect(lambda: self.apply()); self.bFolder.clicked.connect(lambda: self.open_dir(USER_DIR))
        self.fill()

    # ---- list ----
    def cur(self):
        it = self.lst.currentItem(); return MANAGER.get(it.data(Qt.UserRole)) if it else None

    def fill(self, *_, select=None):
        keep = select or (self.cur().id if self.cur() else None); q = self.q.text().lower().strip(); self.lst.blockSignals(True); self.lst.clear()
        for pl in MANAGER.plugins:
            if q and q not in f'{pl.title} {pl.author} {pl.description} {pl.id}'.lower(): continue
            it = QListWidgetItem(QIcon(plugin_pixmap(pl, 44)) if pl.enabled else self._grey(plugin_pixmap(pl, 44)), f"{pl.title}\nby {pl.author}  ·  v{pl.version}" + ('' if pl.enabled else '  ·  disabled'))
            it.setData(Qt.UserRole, pl.id); it.setToolTip(pl.description)
            if not pl.enabled: it.setForeground(QColor(C['mu']))
            self.lst.addItem(it)
        self.lst.blockSignals(False)
        row = next((i for i in range(self.lst.count()) if self.lst.item(i).data(Qt.UserRole) == keep), 0 if self.lst.count() else -1); self.lst.setCurrentRow(row); self.show_plugin(row)

    @staticmethod
    def _grey(pm):
        p = QPainter(pm); p.setCompositionMode(QPainter.CompositionMode_DestinationIn); p.fillRect(pm.rect(), QColor(0, 0, 0, 110)); p.end(); return QIcon(pm)

    def show_plugin(self, _=None):
        pl = self.cur(); self.tree.clear(); self.err.clear()
        for w in (self.bToggle, self.bRemove, self.bOpen): w.setEnabled(bool(pl))
        self.bBase.setVisible(bool(pl and pl.base)); self.bFuncs.setVisible(bool(pl and pl.enabled and pl.catalog_size))
        if not pl:
            self.name.setText('No plugin'); self.by.setText('Install one with the Install button.'); self.desc.setText(''); self.sum.setText(''); self.badges.setText(''); self.pic.clear(); self.err.setVisible(False); return
        self.pic.setPixmap(plugin_pixmap(pl, 96)); self.name.setText(pl.title); self.by.setText(f'by {pl.author}  ·  version {pl.version}'); self.desc.setText(pl.description)
        tag = lambda t, col: f'<span style="background:{col};color:#fff;border-radius:4px;padding:1px 6px"> {t} </span>&nbsp;'
        b = tag('Built-in', '#6b7385') if pl.builtin else tag('Installed', '#3a7bd5')
        b += tag('Enabled', '#2fa66a') if pl.enabled else tag('Disabled', '#7a7f90')
        if pl.has_python: b += tag('Python code', '#c98a2b')
        if pl.base: b += tag('Changes your exlaunch base', '#c98a2b')
        if pl.shadowed: b += tag('Replaces a built-in plugin', '#9a66e8')
        if pl.errors: b += tag(f'{len(pl.errors)} problem' + ('s' if len(pl.errors) != 1 else ''), '#d63c3c')
        self.badges.setText(b); self.sum.setText(pl.summary() + f'   ·   id: {pl.id}')
        if pl.enabled:
            cats = {}
            for d in pl.nodes: cats.setdefault(d['category'], []).append(d)
            for c, ds in cats.items():
                top = QTreeWidgetItem([f'{c}  ({len(ds)})']); top.setIcon(0, icon('group', 'mu', 16)); self.tree.addTopLevelItem(top)
                for d in ds: ch = QTreeWidgetItem([d['label']]); ch.setToolTip(0, d['description']); top.addChild(ch)
                top.setExpanded(len(cats) == 1 or len(ds) <= 8)
            if pl.catalog_size:
                cat = PN.CATALOG.get(pl.id); top = QTreeWidgetItem([f'Function catalog  ({pl.catalog_size})']); top.setIcon(0, icon('func', 'mu', 16)); self.tree.addTopLevelItem(top)
                kinds = {}
                for e in (cat['entries'] if cat else []): kinds[e.get('c', '').split(':')[0] or 'Other'] = kinds.get(e.get('c', '').split(':')[0] or 'Other', 0) + 1
                for k, n in sorted(kinds.items()): top.addChild(QTreeWidgetItem([f'{k}  ({n})']))
                top.setToolTip(0, 'Browse and add them with Edit > Add plugin function (Ctrl+Shift+K)')
            if pl.templates:
                top = QTreeWidgetItem([f'Templates  ({len(pl.templates)})  - File > New from template']); self.tree.addTopLevelItem(top)
                for nm, _p, ds in pl.templates: ch = QTreeWidgetItem([nm]); ch.setToolTip(0, ds); top.addChild(ch)
                top.setExpanded(True)
            if pl.themes:
                top = QTreeWidgetItem([f'Themes  ({len(pl.themes)})']); top.setIcon(0, icon('palette', 'mu', 16)); self.tree.addTopLevelItem(top)
                for _k, nm in pl.themes: top.addChild(QTreeWidgetItem([nm]))
                top.setExpanded(True)
            if pl.actions:
                top = QTreeWidgetItem([f'Menu actions  ({len(pl.actions)})']); self.tree.addTopLevelItem(top)
                for a in pl.actions: top.addChild(QTreeWidgetItem([a[0]]))
        else: self.tree.addTopLevelItem(QTreeWidgetItem(['Disabled: enable it to use its content.']))
        self.err.setVisible(bool(pl.errors)); self.err.setPlainText('\n'.join(pl.errors))
        self.bToggle.setText('Disable' if pl.enabled else 'Enable'); self.bRemove.setEnabled(not pl.builtin); self.bRemove.setToolTip('Bundled plugins cannot be removed, only disabled.' if pl.builtin else 'Delete this plugin from your plugins folder')

    # ---- actions ----
    def apply(self, select=None):
        self.reload(); self.changed.emit(); self.fill(select=select)

    def toggle(self):
        pl = self.cur()
        if not pl: return
        turn_on = not pl.enabled; MANAGER.set_enabled(self.cfg, pl.id, turn_on); self.apply(select=pl.id); win = self.parent()
        if pl.base and win is not None and hasattr(win, 'offer_base'):
            if turn_on: win.offer_base(MANAGER.get(pl.id))
            else: BD.offer_remove(win, pl)
        self.fill(select=pl.id)

    def base_dialog(self):
        pl = self.cur()
        if pl and pl.base: BD.BaseDialog(self.parent(), pl).exec()

    def open_funcs(self):
        pl, win = self.cur(), self.parent()
        if pl and win is not None and hasattr(win, 'add_plugin_function'): self.accept(); QTimer.singleShot(0, lambda: win.add_plugin_function(None, pl.id))

    def remove(self):
        pl = self.cur()
        if not pl or pl.builtin: return
        if QMessageBox.question(self, 'Remove plugin', f'Delete the plugin "{pl.title}" and its files?\nNodes already used in your graph keep working (a copy of their definition is saved in the graph).') != QMessageBox.Yes: return
        try: MANAGER.remove(pl.id)
        except Exception as e: QMessageBox.warning(self, 'Remove plugin', str(e)); return
        self.apply()

    def _install(self, src):
        if MANAGER.has_python(src) and QMessageBox.warning(self, 'Plugin with Python code', 'This plugin contains Python code (plugin.py). It runs with the same rights as this program: it can read and write your files.\n\nOnly install plugins from people you trust. Install anyway?',
                                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes: return
        try: pid = MANAGER.install(src)
        except Exception as e: QMessageBox.warning(self, 'Install plugin', str(e)); return
        self.apply(select=pid)

    def install_file(self):
        f, _ = QFileDialog.getOpenFileName(self, 'Install a plugin', '', 'Plugin archive (*.zip *.odnp);;All files (*)')
        if f: self._install(f)

    def install_dir(self):
        d = QFileDialog.getExistingDirectory(self, 'Choose the plugin folder (the one holding plugin.json)')
        if d: self._install(d)

    def new_plugin(self):
        d = NewPluginDialog(self)
        if not d.exec(): return
        pid = MANAGER.create(d.title.text().strip(), d.author.text().strip(), d.desc.text().strip()); self.apply(select=pid)
        QMessageBox.information(self, 'New plugin', f'Created in:\n{USER_DIR / pid}\n\nEdit plugin.json (and add an icon.png), then press Reload.')

    @staticmethod
    def open_dir(p):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))
