"""Reusable widgets: C++ highlighter, block palette, inspector, build runner."""
import os, re
from html import escape
from PySide6.QtCore import QMimeData, QObject, QProcess, Qt, Signal
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .graph import COMMON_TYPES, E, GRP, NODE_FIELDS, PRE
from .valueedit import make_editor


# ---------------- C++ highlighting ----------------
class CppHighlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        def fmt(c, bold=False):
            f = QTextCharFormat(); f.setForeground(QColor(c)); f.setFontWeight(QFont.Bold if bold else QFont.Normal); return f
        kw = r'\b(static|void|return|if|else|switch|case|default|break|for|while|int|float|bool|auto|const|extern|reinterpret_cast|static_cast|nullptr|true|false|u8|u32|s32|f32|class|struct)\b'
        self.rules = [(re.compile(r'\b(0x[0-9a-fA-F]+|\d+\.?\d*f?)\b'), fmt('#6dd26d')), (re.compile(kw), fmt('#6aa7ff', True)), (re.compile(r'^\s*#\w+'), fmt('#c792ea')),
                      (re.compile(r'"[^"]*"'), fmt('#e6b673')), (re.compile(r'//.*|/\*.*?\*/'), fmt('#7f8aa3'))]

    def highlightBlock(self, text):
        for rx, f in self.rules:
            for m in rx.finditer(text): self.setFormat(m.start(), m.end() - m.start(), f)


# ---------------- block palette ----------------
class DragTree(QTreeWidget):
    def mimeData(self, items):
        m = QMimeData(); m.setText(items[0].data(0, Qt.UserRole) or ''); return m


class Palette(QWidget):
    add_pre = Signal(str)  # palette name
    browse = Signal()      # open the game function browser

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(8, 8, 8, 8); v.setSpacing(8)
        self.btn = QPushButton('＋  Game function…'); self.btn.setObjectName('pri'); self.btn.setToolTip('Search the game for a function to call or hook (Ctrl+F)'); v.addWidget(self.btn)
        hint = QLabel('Call or hook any function of Super Mario Odyssey.'); hint.setWordWrap(True); hint.setStyleSheet('color:#8a91a5'); v.addWidget(hint)
        self.filter = QLineEdit(); self.filter.setPlaceholderText('Filter blocks…'); self.filter.setClearButtonEnabled(True); v.addWidget(self.filter)
        self.tree = DragTree(); self.tree.setHeaderHidden(True); self.tree.setDragEnabled(True); v.addWidget(self.tree, 1)
        tip = QLabel('Double-click or drag a block onto the canvas.'); tip.setWordWrap(True); tip.setStyleSheet('color:#8a91a5'); v.addWidget(tip)
        for g, items in GRP.items():
            top = QTreeWidgetItem([g]); top.setFlags(Qt.ItemIsEnabled); self.tree.addTopLevelItem(top)
            for k in items:
                c = QTreeWidgetItem([k]); c.setData(0, Qt.UserRole, 'odn:pre:' + k); c.setToolTip(0, PRE[k][3]); top.addChild(c)
        self.tree.expandAll()
        self.btn.clicked.connect(self.browse.emit); self.filter.textChanged.connect(self._filter)
        self.tree.itemDoubleClicked.connect(lambda it, _=0: self.add_pre.emit(it.data(0, Qt.UserRole)[8:]) if it.data(0, Qt.UserRole) else None)

    def _filter(self, text):
        q = text.lower().strip()
        for i in range(self.tree.topLevelItemCount()):
            top, any_ = self.tree.topLevelItem(i), False
            for j in range(top.childCount()):
                c = top.child(j); hide = bool(q) and q not in c.text(0).lower() and q not in PRE[c.text(0)][3].lower(); c.setHidden(hide); any_ |= not hide
            top.setHidden(not any_)


# ---------------- inspector ----------------
class Inspector(QScrollArea):
    changed = Signal()       # a setting changed (pins may change)
    valuechanged = Signal()  # a fixed input value changed
    action = Signal(str)     # 'dup' | 'del' | 'unlink' | 'edit'

    def __init__(self, graph):
        super().__init__(); self.graph, self.nid = graph, 0; self.setWidgetResizable(True); self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget(); self.setWidget(body); v = QVBoxLayout(body); v.setContentsMargins(12, 12, 12, 12); v.setSpacing(10)
        self.help = QLabel('Select a node to see and edit its properties.\n\nTip: double-click an empty spot of the canvas to add a game function, or right-click for all blocks.')
        self.help.setWordWrap(True); self.help.setStyleSheet('color:#8a91a5'); v.addWidget(self.help)
        self.title = QLabel(); self.title.setWordWrap(True); self.title.setTextInteractionFlags(Qt.TextSelectableByMouse); self.title.setStyleSheet('font-size:15px;font-weight:600'); v.addWidget(self.title)
        self.kind = QLabel(); self.kind.setWordWrap(True); self.kind.setStyleSheet('color:#8a91a5'); v.addWidget(self.kind)
        # game function details
        self.fn_box = QGroupBox('Game function'); f = QFormLayout(self.fn_box); f.setLabelAlignment(Qt.AlignTop)
        self.f_sig = QLabel(); self.f_sig.setWordWrap(True); self.f_sig.setTextInteractionFlags(Qt.TextSelectableByMouse); self.f_sig.setStyleSheet('font-family:Consolas,monospace')
        self.f_ret, self.f_off, self.f_status = QLabel(), QLabel(), QLabel(); self.f_sym = QLineEdit(); self.f_sym.setReadOnly(True); self.f_sym.setStyleSheet('font-family:Consolas,monospace;font-size:11px')
        f.addRow(self.f_sig); f.addRow('Returns', self.f_ret); f.addRow('Offset', self.f_off); f.addRow('Symbol', self.f_sym); f.addRow('Status', self.f_status)
        self.bEdit = QPushButton('Edit this block…'); self.bEdit.clicked.connect(lambda: self.action.emit('edit')); f.addRow(self.bEdit); v.addWidget(self.fn_box)
        self.set_box = QGroupBox('Settings'); self.set_form = QFormLayout(self.set_box); self.set_form.setRowWrapPolicy(QFormLayout.WrapAllRows); v.addWidget(self.set_box)
        self.in_box = QGroupBox('Inputs'); self.in_form = QFormLayout(self.in_box); self.in_form.setRowWrapPolicy(QFormLayout.WrapAllRows); v.addWidget(self.in_box)
        self.out_box = QGroupBox('Outputs'); self.out_form = QFormLayout(self.out_box); v.addWidget(self.out_box)
        row = QHBoxLayout()
        for k, t in (('dup', 'Duplicate'), ('unlink', 'Disconnect'), ('del', 'Delete')):
            b = QPushButton(t); b.clicked.connect(lambda _=0, k=k: self.action.emit(k)); row.addWidget(b)
        self.btns = QWidget(); self.btns.setLayout(row); v.addWidget(self.btns); v.addStretch(1)
        self.sections = [self.title, self.kind, self.fn_box, self.set_box, self.in_box, self.out_box, self.btns]; self.show_node(0)

    @staticmethod
    def _clear(form):
        while form.rowCount(): form.removeRow(0)

    def show_node(self, nid):
        self.nid = nid if nid in self.graph.nodes else 0; self._clear(self.set_form); n = self.graph.nodes.get(self.nid)
        self.help.setVisible(not n)
        if not n:
            for w in self.sections: w.setVisible(False)
            return
        for fd in NODE_FIELDS.get(n.type, []):
            if fd.key == 'save' and n.type == 'callgame' and self.graph.sg(n)['r'] == 'void': continue  # nothing to save
            self.set_form.addRow(fd.label, self._field(n, fd))
        self.refresh()

    def _field(self, n, fd):
        val = n.f.get(fd.key, '')
        if fd.kind == 'choice':
            w = QComboBox()
            for key, lab in fd.opts: w.addItem(lab, key)
            w.setCurrentIndex(max(0, w.findData(val))); w.currentIndexChanged.connect(lambda _, w=w, k=fd.key: self._set(k, w.currentData())); return w
        if fd.kind == 'bool':
            w = QCheckBox(); w.setChecked(bool(val)); w.toggled.connect(lambda b, k=fd.key: self._set(k, b)); return w
        if fd.kind in ('type', 'var', 'func'):
            w = QComboBox(); w.setEditable(True); items = COMMON_TYPES if fd.kind == 'type' else self.graph.variable_names() if fd.kind == 'var' else self.graph.function_names()
            w.addItems(items); w.setEditText(str(val)); w.setInsertPolicy(QComboBox.NoInsert)
            if fd.kind != 'type': w.setPlaceholderText('choose or type a name'); w.setCurrentIndex(w.findText(str(val)))
            w.setEditText(str(val)); w.currentTextChanged.connect(lambda t, k=fd.key: self._set(k, t)); return w
        w = QLineEdit(str(val)); w.setPlaceholderText(fd.hint); w.textEdited.connect(lambda t, k=fd.key: self._set(k, t)); return w

    def refresh(self):
        """Update title, function details, inputs and outputs (settings widgets are left untouched)."""
        n = self.graph.nodes.get(self.nid)
        if not n: return
        g = self.graph; title, ins, outs = g.spec(n)
        for w in (self.title, self.kind, self.btns): w.setVisible(True)
        self.title.setText(title); self.kind.setText(g.category(n)); game = n.type in ('hook', 'callgame')
        self.fn_box.setVisible(game)
        if game:
            c = g.sg(n); known = n.f.get('sym') in g.cat
            self.f_sig.setText(f"{c['r']} {c['n']}({', '.join(c['p'])})" if known else 'Symbol not found in the catalog'); self.f_ret.setText(c['r'] if known else '?')
            self.f_off.setText(f"0x{c['o']:x}" if known else '?'); self.f_sym.setText(n.f.get('sym', '')); self.f_sym.setCursorPosition(0)
            self.f_status.setText(('Matching (decompiled)' if c['st'] == 'M' else 'Not matching / not decompiled yet') if known else '?')
        self.set_box.setVisible(self.set_form.rowCount() > 0)
        self._clear(self.in_form); self._clear(self.out_form)
        hint = QLabel('Connect a node, or type a fixed value.'); hint.setStyleSheet('color:#8a91a5'); hint.setWordWrap(True); self.in_form.addRow(hint)
        for p in ins:
            if p.type == E: continue
            lab = QLabel(f'<b>{escape(p.label)}</b><br><span style="color:#8a91a5">{escape(p.type or "any type")}</span>')
            if g.linked(n.id, p.id, 'i'):
                w = QLabel('connected to another node'); w.setStyleSheet('color:#8a91a5;font-style:italic')
            else: w = make_editor(p.type, n.d.get(p.id, ''), lambda raw, pid=p.id: self._dflt(pid, raw))
            self.in_form.addRow(lab, w)
        for p in outs:
            if p.type == E: continue
            self.out_form.addRow(QLabel(f'<b>{escape(p.label)}</b>'), QLabel(f'<span style="color:#8a91a5">{escape(p.type or "any type")}</span>'))
        self.in_box.setVisible(self.in_form.rowCount() > 1); self.out_box.setVisible(self.out_form.rowCount() > 0)
        self.out_box.setTitle('Outputs' + ('  (values the game gives to your hook)' if n.type == 'hook' else ''))

    def _set(self, k, v):
        n = self.graph.nodes.get(self.nid)
        if n and n.f.get(k) != v: n.f[k] = v; self.changed.emit()

    def _dflt(self, pin, v):
        n = self.graph.nodes.get(self.nid)
        if n: n.d[pin] = v; self.valuechanged.emit()


# ---------------- build ----------------
class BuildRunner(QObject):
    output = Signal(str)
    done = Signal(int)

    def __init__(self):
        super().__init__(); self.p = None

    def running(self): return self.p is not None

    def start(self, cmd, cwd):
        if self.p: return
        self.p = QProcess(self); self.p.setProcessChannelMode(QProcess.MergedChannels)
        if cwd: self.p.setWorkingDirectory(cwd)
        if os.name == 'nt': self.p.setProgram('cmd.exe'); self.p.setNativeArguments(f'/S /C "chcp 65001>nul & {cmd}"')
        else: self.p.setProgram('/bin/sh'); self.p.setArguments(['-c', cmd])
        self.p.readyRead.connect(lambda: self.output.emit(bytes(self.p.readAll()).decode('utf-8', 'replace')))
        self.p.errorOccurred.connect(self._err); self.p.finished.connect(self._fin); self.p.start()

    def _err(self, e):
        if e == QProcess.FailedToStart: self.output.emit('Could not start the command.\n'); self._fin(1)

    def _fin(self, code, *_):
        if self.p: p, self.p = self.p, None; p.deleteLater(); self.done.emit(int(code))

    def stop(self):
        if self.p: self.p.kill()
