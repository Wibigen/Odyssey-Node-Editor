"""Game function browser and block builder (search the catalog, set arguments, choose call or hook)."""
from collections import Counter
from html import escape
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QRadioButton, QScrollArea,
                               QSplitter, QStackedWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .graph import IDENT, MODES, argname
from .valueedit import make_editor

MAX_ROWS = 500


class ArgRow(QFrame):
    """One argument of a call: wired from another node, or given a fixed value."""

    def __init__(self, label, t, value=''):
        super().__init__(); self.setObjectName('row'); self.v = value or ''
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 8, 10, 8); lay.setSpacing(6)
        head = QHBoxLayout(); lab = QLabel(f'<b>{escape(label)}</b>  <span style="color:#8a91a5">{escape(t)}</span>'); lab.setWordWrap(True); head.addWidget(lab, 1)
        self.mode = QComboBox(); self.mode.addItem('Connect a node', 0); self.mode.addItem('Fixed value', 1); head.addWidget(self.mode); lay.addLayout(head)
        self.editor = make_editor(t, self.v, self._set); lay.addWidget(self.editor)
        self.mode.setCurrentIndex(1 if self.v else 0); self.editor.setVisible(bool(self.v)); self.mode.currentIndexChanged.connect(lambda i: self.editor.setVisible(i == 1))

    def _set(self, raw): self.v = raw
    def raw(self): return self.v if self.mode.currentIndex() == 1 else ''


class FunctionDialog(QDialog):
    def __init__(self, catalog, parent=None, node=None, graph=None):
        super().__init__(parent); self.cat, self.node, self.graph, self.cur, self.rows = catalog, node, graph, None, []
        self.names = [c['n'].lower() for c in catalog]; self.setWindowTitle('Edit game function block' if node else 'Add a game function'); self.resize(1120, 720)
        outer = QVBoxLayout(self); split = QSplitter(); outer.addWidget(split, 1)
        # ---- left: search ----
        self.left = QWidget(); l = QVBoxLayout(self.left); l.setContentsMargins(0, 0, 8, 0)
        self.q = QLineEdit(); self.q.setPlaceholderText('Search by name…  e.g. setTrans, exePlay, PlayerActorHakoniwa::'); self.q.setClearButtonEnabled(True); l.addWidget(self.q)
        row = QHBoxLayout(); self.grp = QComboBox(); self.grp.addItem(f'All groups ({len(catalog)})', '')
        for p, n in Counter(c['n'].split('::')[0] for c in catalog if '::' in c['n']).most_common(40): self.grp.addItem(f'{p}  ({n})', p)
        self.only = QCheckBox('Only decompiled (matching)'); row.addWidget(self.grp, 1); row.addWidget(self.only); l.addLayout(row)
        self.tree = QTreeWidget(); self.tree.setColumnCount(4); self.tree.setHeaderLabels(['Function', 'Returns', 'Args', 'Status']); self.tree.setRootIsDecorated(False); self.tree.setUniformRowHeights(True)
        self.tree.setColumnWidth(0, 330); self.tree.setColumnWidth(1, 90); self.tree.setColumnWidth(2, 40); l.addWidget(self.tree, 1)
        self.count = QLabel(); self.count.setStyleSheet('color:#8a91a5'); l.addWidget(self.count); split.addWidget(self.left)
        # ---- right: details + block builder ----
        right = QWidget(); r = QVBoxLayout(right); r.setContentsMargins(8, 0, 0, 0)
        self.name = QLabel('Select a function on the left'); self.name.setWordWrap(True); self.name.setTextInteractionFlags(Qt.TextSelectableByMouse); self.name.setStyleSheet('font-size:16px;font-weight:600'); r.addWidget(self.name)
        self.sig = QLabel(); self.sig.setWordWrap(True); self.sig.setTextInteractionFlags(Qt.TextSelectableByMouse); self.sig.setStyleSheet('font-family:Consolas,monospace'); r.addWidget(self.sig)
        info = QFormLayout(); self.i_ret, self.i_off, self.i_status = QLabel(), QLabel(), QLabel(); self.i_sym = QLineEdit(); self.i_sym.setReadOnly(True); self.i_sym.setStyleSheet('font-family:Consolas,monospace;font-size:11px')
        info.addRow('Returns', self.i_ret); info.addRow('Offset', self.i_off); info.addRow('Symbol', self.i_sym); info.addRow('Status', self.i_status); r.addLayout(info)
        self.rCall = QRadioButton('Call this function from my mod'); self.rHook = QRadioButton('Hook this function  (my graph runs whenever the game calls it)'); self.rCall.setChecked(True); r.addWidget(self.rCall); r.addWidget(self.rHook)
        self.stack = QStackedWidget(); r.addWidget(self.stack, 1)
        call = QWidget(); cl = QVBoxLayout(call); cl.setContentsMargins(0, 4, 0, 0)
        self.args_hint = QLabel(); self.args_hint.setWordWrap(True); self.args_hint.setStyleSheet('color:#8a91a5'); cl.addWidget(self.args_hint)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.args_w = QWidget(); self.args_l = QVBoxLayout(self.args_w); self.args_l.setContentsMargins(0, 0, 6, 0); self.args_l.addStretch(1); sc.setWidget(self.args_w); cl.addWidget(sc, 1)
        sv = QHBoxLayout(); self.save_l = QLabel('Save the result in a variable named'); self.save = QLineEdit(); self.save.setPlaceholderText('optional, e.g. pos'); sv.addWidget(self.save_l); sv.addWidget(self.save, 1); cl.addLayout(sv)
        hook = QWidget(); hl = QFormLayout(hook); self.mode = QComboBox()
        for k, lab in MODES: self.mode.addItem(lab, k)
        self.ret = QLineEdit(); self.ret.setPlaceholderText('empty = same as the game function'); hl.addRow('When to run my graph', self.mode); hl.addRow('Return type override', self.ret)
        note = QLabel('Inside a hook, the arguments the game passes (arg 1, arg 2…) are available as outputs of the hook node, and the original result when you choose "original first".')
        note.setWordWrap(True); note.setStyleSheet('color:#8a91a5'); hl.addRow(note); self.stack.addWidget(call); self.stack.addWidget(hook); split.addWidget(right); split.setStretchFactor(0, 5); split.setStretchFactor(1, 4); split.setSizes([560, 520])
        self.err = QLabel(); self.err.setStyleSheet('color:#ef5b5b'); outer.addWidget(self.err)
        self.bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); self.ok = self.bb.button(QDialogButtonBox.Ok); self.ok.setText('Apply' if node else 'Add to graph'); self.ok.setObjectName('pri'); outer.addWidget(self.bb)
        self.bb.accepted.connect(self.try_accept); self.bb.rejected.connect(self.reject)
        self.rCall.toggled.connect(lambda c: self.stack.setCurrentIndex(0 if c else 1))
        self.q.textChanged.connect(self.refresh); self.grp.currentIndexChanged.connect(self.refresh); self.only.toggled.connect(self.refresh)
        self.tree.currentItemChanged.connect(lambda it, _: self.select(self.cat[it.data(0, Qt.UserRole)]) if it else None); self.tree.itemDoubleClicked.connect(lambda *_: self.try_accept())
        if node: self.start_edit()
        else: self.refresh(); self.q.setFocus()
        self.ok.setEnabled(self.cur is not None)

    # ---------- search ----------
    def refresh(self):
        q, grp, only = self.q.text().lower().strip(), self.grp.currentData(), self.only.isChecked(); hits = []
        for i, n in enumerate(self.names):
            if q and q not in n: continue
            if grp and not self.cat[i]['n'].startswith(grp + '::'): continue
            if only and self.cat[i]['st'] != 'M': continue
            hits.append(i)
        def key(i):
            n = self.names[i]; s = n.rsplit('::', 1)[-1]; return (0 if s == q else 1 if s.startswith(q) else 2, len(n), n)
        hits.sort(key=key); self.tree.clear()
        for i in hits[:MAX_ROWS]:
            c = self.cat[i]; it = QTreeWidgetItem([c['n'], c['r'], str(len(c['p'])), 'matching' if c['st'] == 'M' else 'not matched']); it.setData(0, Qt.UserRole, i)
            it.setToolTip(0, f"{c['r']} {c['n']}({', '.join(c['p'])})"); self.tree.addTopLevelItem(it)
        self.count.setText(f'{len(hits)} function(s)' + (f' - showing the first {MAX_ROWS}, refine your search' if len(hits) > MAX_ROWS else ''))
        if hits: self.tree.setCurrentItem(self.tree.topLevelItem(0))
        else: self.cur = None; self.ok.setEnabled(False)

    # ---------- details / block builder ----------
    def select(self, c, preset=None):
        self.cur = c; preset = preset or {}; self.err.setText(''); self.ok.setEnabled(True)
        self.name.setText(c['n']); self.sig.setText(f"{c['r']} {c['n']}({', '.join(c['p'])})"); self.i_ret.setText(c['r']); self.i_off.setText(f"0x{c['o']:x}"); self.i_sym.setText(c['s']); self.i_sym.setCursorPosition(0)
        self.i_status.setText('Matching (decompiled)' if c['st'] == 'M' else 'Not matching / not decompiled yet')
        while len(self.rows): r = self.rows.pop(); r.setParent(None); r.deleteLater()
        for i, t in enumerate(c['p']):
            row = ArgRow(argname(c, i), t, preset.get(f'a{i}', '')); self.rows.append(row); self.args_l.insertWidget(self.args_l.count() - 1, row)
        self.args_hint.setText(f"This function takes {len(c['p'])} argument(s). For each one, connect a node or type a fixed value." if c['p'] else 'This function takes no arguments.')
        self.save.setVisible(c['r'] != 'void'); self.save_l.setVisible(c['r'] != 'void')

    def start_edit(self):
        n, g = self.node, self.graph; self.left.setVisible(False); c = g.cat.get(n.f.get('sym'))
        (self.rHook if n.type == 'hook' else self.rCall).setChecked(True); self.rCall.setEnabled(False); self.rHook.setEnabled(False)
        self.mode.setCurrentIndex(max(0, self.mode.findData(n.f.get('mode')))); self.ret.setText(n.f.get('ret', '')); self.save.setText(n.f.get('save', ''))
        if c: self.select(c, n.d)
        else: self.name.setText('Unknown symbol: ' + str(n.f.get('sym'))); self.err.setText('This symbol is not in the catalog (extract it again in Settings).'); self.ok.setEnabled(False)

    def try_accept(self):
        if self.cur is None: return
        s = self.save.text().strip()
        if self.rCall.isChecked() and s and not IDENT.match(s): self.err.setText(f'"{s}" is not a valid C++ variable name.'); return
        self.accept()

    def result(self):
        """(node type, fields, fixed input values)"""
        s = self.cur['s']
        if self.rHook.isChecked(): return 'hook', {'sym': s, 'mode': self.mode.currentData(), 'ret': self.ret.text().strip()}, {}
        return 'callgame', {'sym': s, 'save': self.save.text().strip()}, {f'a{i}': r.raw() for i, r in enumerate(self.rows) if r.raw()}
