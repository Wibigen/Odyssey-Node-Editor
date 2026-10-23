"""Plugin function browser: search the function catalogs of the enabled plugins (Dear ImGui...) and add them to the graph as nodes."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .i18n import tr
from . import plugnodes as PN
from .icons import bind
from .theme import C

KIND_TAG = {'f': 'function', 'c': 'constant', 'm': 'method'}


class PluginFunctionDialog(QDialog):
    """Emits chosen(pid) for every function added. 'Keep open' lets you add several without reopening."""
    chosen = Signal(str)

    def __init__(self, parent=None, start_plugin=''):
        super().__init__(parent); self.setWindowTitle('Plugin function browser'); self.resize(900, 620); self.setMinimumSize(640, 420); self.picked = None
        v = QVBoxLayout(self); top = QHBoxLayout(); self.q = QLineEdit(); self.q.setPlaceholderText('Search a function, a constant or a word of its description…'); self.q.setClearButtonEnabled(True); top.addWidget(self.q, 1)
        self.plug = QComboBox(); self.plug.addItem('All plugins', ''); [self.plug.addItem(c['title'], k) for k, c in PN.CATALOG.items()]; top.addWidget(self.plug)
        self.kind = QComboBox(); [self.kind.addItem(t, k) for t, k in (('Everything', ''), ('Functions', 'f'), ('Methods', 'm'), ('Constants', 'c'))]; top.addWidget(self.kind); v.addLayout(top)
        sp = QSplitter(); v.addWidget(sp, 1); self.tree = QTreeWidget(); self.tree.setHeaderHidden(True); self.tree.setUniformRowHeights(True); sp.addWidget(self.tree)
        right = QWidget(); rv = QVBoxLayout(right); rv.setContentsMargins(10, 0, 0, 0); self.name = QLabel(); self.name.setStyleSheet('font-size:16px;font-weight:600'); self.name.setWordWrap(True); rv.addWidget(self.name)
        self.cat = QLabel(); self.cat.setStyleSheet(f"color:{C['mu']}"); rv.addWidget(self.cat)
        self.sig = QPlainTextEdit(); self.sig.setReadOnly(True); self.sig.setMaximumHeight(96); f = QFont('Consolas'); f.setStyleHint(QFont.Monospace); self.sig.setFont(f); rv.addWidget(self.sig)
        self.doc = QLabel(); self.doc.setWordWrap(True); self.doc.setAlignment(Qt.AlignTop | Qt.AlignLeft); self.doc.setTextInteractionFlags(Qt.TextSelectableByMouse); rv.addWidget(self.doc, 1)
        self.hint = QLabel(); self.hint.setWordWrap(True); self.hint.setStyleSheet(f"color:{C['mu']}"); rv.addWidget(self.hint); sp.addWidget(right); sp.setStretchFactor(0, 1); sp.setStretchFactor(1, 1); sp.setSizes([430, 470])
        bot = QHBoxLayout(); self.count = QLabel(); self.count.setStyleSheet(f"color:{C['mu']}"); bot.addWidget(self.count); bot.addStretch(1)
        self.keep = QCheckBox('Keep open to add several'); bot.addWidget(self.keep); self.bAdd = QPushButton('Add to the graph'); self.bAdd.setObjectName('pri'); bind(self.bAdd, 'plus', '#ffffff', 16); self.bAdd.setDefault(True); bot.addWidget(self.bAdd)
        close = QPushButton('Close'); close.clicked.connect(self.reject); bot.addWidget(close); v.addLayout(bot)
        self.q.textChanged.connect(self.fill); self.plug.currentIndexChanged.connect(self.fill); self.kind.currentIndexChanged.connect(self.fill)
        self.tree.currentItemChanged.connect(self.show_entry); self.tree.itemDoubleClicked.connect(lambda *_: self.add()); self.bAdd.clicked.connect(self.add)
        if start_plugin and self.plug.findData(start_plugin) >= 0: self.plug.setCurrentIndex(self.plug.findData(start_plugin))
        self.fill(); self.q.setFocus()

    def entries(self):
        q = self.q.text().lower().strip(); words = q.split(); pk, kd = self.plug.currentData(), self.kind.currentData()
        for k, cat in PN.CATALOG.items():
            if pk and k != pk: continue
            for e in cat['entries']:
                if kd and e.get('kind', 'f') != kd: continue
                if words:
                    hay = f"{e.get('label', e['id'])} {e['call']} {e.get('c', '')} {e.get('d', '')}".lower()
                    if not all(w in hay for w in words): continue
                yield k, cat, e

    def fill(self, *_):
        self.tree.setUpdatesEnabled(False); self.tree.clear(); tops, n, best = {}, 0, (9, None); searching = bool(self.q.text().strip()); words = self.q.text().lower().split(); flat = ''.join(words)
        multi = len(PN.CATALOG) > 1 and not self.plug.currentData()
        for k, cat, e in self.entries():
            key = ((cat['title'] + ' › ') if multi else '') + (e.get('c') or cat['title'])
            top = tops.get(key)
            if top is None: top = tops[key] = QTreeWidgetItem([key]); top.setFlags(Qt.ItemIsEnabled); self.tree.addTopLevelItem(top)
            it = QTreeWidgetItem([e.get('label') or e['id']]); it.setData(0, Qt.UserRole, f"{k}:{e['id']}"); it.setToolTip(0, PN._sig(e)); top.addChild(it); n += 1
            lab = (e.get('label') or e['id']).lower(); sc = 0 if lab == flat else 1 if lab.startswith(flat) else 2 if words and all(w in lab for w in words) else 3
            if searching and sc < best[0]: best = (sc, it)
        for key, top in tops.items(): top.setText(0, f'{key}  ({top.childCount()})'); top.setExpanded(searching and n < 300)
        self.tree.sortItems(0, Qt.AscendingOrder) if False else None
        self.tree.setUpdatesEnabled(True); self.count.setText(tr('{0} result(s)', n) if searching or self.plug.currentData() or self.kind.currentData() else tr('{0} entries', n))
        first = best[1] if best[1] is not None else next((top.child(0) for top in tops.values() if top.isExpanded() and top.childCount()), None)
        if first is not None: first.parent().setExpanded(True)
        if first: self.tree.setCurrentItem(first)
        else: self.show_entry(None)

    def cur_pid(self):
        it = self.tree.currentItem(); return it.data(0, Qt.UserRole) if it else None

    def show_entry(self, it, _prev=None):
        pid = it.data(0, Qt.UserRole) if it else None; d = PN.catalog_def(pid) if pid else None; self.bAdd.setEnabled(bool(d))
        if not d:
            self.name.setText(''); self.cat.setText(''); self.sig.clear(); self.doc.setText('Choose a function on the left.' if self.tree.topLevelItemCount() else 'Nothing matches.'); self.hint.setText(''); return
        pl, eid = pid.split(':', 1); e = PN.CATALOG[pl]['by_id'][eid]; kind = e.get('kind', 'f')
        self.name.setText(d['label']); self.cat.setText(f"{KIND_TAG[kind].capitalize()} · {d['category']} · {d['plugin_title']}")
        self.sig.setPlainText(PN._sig(e) if kind != 'c' else e['call']); self.doc.setText(e.get('d') or 'No description.')
        inc = ', '.join(d['includes']); bits = []
        if kind == 'm': bits.append('Method: plug the object (for example the result of GetWindowDrawList) into the "object" input.')
        if d['both']: bits.append('Right-click the node > "Use as a value" to use the result directly inside another node.')
        if e.get('va'): bits.append('Variable arguments: set their number in the inspector (like printf).')
        if any('*' in p[0] and 'char' not in p[0] for p in e.get('p') or []): bits.append('Pointer inputs: type &variable (or use the "Address of" node).')
        self.hint.setText('\n'.join(bits + ([tr('Adds #include {0}', inc)] if inc else [])))

    def add(self):
        pid = self.cur_pid()
        if not pid: return
        self.picked = pid; self.chosen.emit(pid)
        if not self.keep.isChecked(): self.accept()
