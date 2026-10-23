"""Reusable widgets: C++ highlighter, block palette, inspector, build runner."""
from .i18n import tr
import os, re
from html import escape
from PySide6.QtCore import QMimeData, QObject, QProcess, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QScrollArea, QToolButton,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .shells import invocation
from . import plugnodes as PN
from .theme import C
from .icons import bind
from .graph import ADV_KEYS, CALLS, COMMON_TYPES, E, GRP, NODE_FIELDS, PRE, QUALS, fields_for, parse_params, split_top
from .rettype import ask_ret_type, remember
from .valueedit import make_editor


# ---------------- C++ highlighting ----------------
class _Gutter(QWidget):
    def __init__(self, ed): super().__init__(ed); self.ed = ed
    def sizeHint(self): return QSize(self.ed.gutter_width(), 0)
    def paintEvent(self, ev): self.ed.paint_gutter(ev)


class CodeEdit(QPlainTextEdit):
    """Read-only code view with line numbers (they match the lines the Problems / highlight refer to)."""
    def __init__(self):
        super().__init__(); self._numbers = True; self.gutter = _Gutter(self)
        self.blockCountChanged.connect(self._margin); self.updateRequest.connect(self._scroll); self._margin()

    def set_numbers(self, on): self._numbers = bool(on); self.gutter.setVisible(self._numbers); self._margin(); self.gutter.update()

    def gutter_width(self): return 0 if not self._numbers else 14 + self.fontMetrics().horizontalAdvance('9') * max(3, len(str(self.blockCount())))
    def _margin(self, *_): self.setViewportMargins(self.gutter_width(), 0, 0, 0)
    def _scroll(self, rect, dy):
        if dy: self.gutter.scroll(0, dy)
        else: self.gutter.update(0, rect.y(), self.gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()): self._margin()

    def resizeEvent(self, ev):
        super().resizeEvent(ev); cr = self.contentsRect(); self.gutter.setGeometry(QRect(cr.left(), cr.top(), self.gutter_width(), cr.height()))

    def paint_gutter(self, ev):
        p = QPainter(self.gutter); p.fillRect(ev.rect(), QColor(C['bg2'])); p.setPen(QColor(C['mu'])); p.setFont(self.font())
        b = self.firstVisibleBlock(); n = b.blockNumber(); top = round(self.blockBoundingGeometry(b).translated(self.contentOffset()).top()); bottom = top + round(self.blockBoundingRect(b).height())
        while b.isValid() and top <= ev.rect().bottom():
            if b.isVisible() and bottom >= ev.rect().top(): p.drawText(0, top, self.gutter.width() - 8, self.fontMetrics().height(), Qt.AlignRight, str(n + 1))
            b = b.next(); top = bottom; bottom = top + round(self.blockBoundingRect(b).height()); n += 1


class CppHighlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        def fmt(c, bold=False):
            f = QTextCharFormat(); f.setForeground(QColor(c)); f.setFontWeight(QFont.Bold if bold else QFont.Normal); return f
        kw = r'\b(static|void|return|if|else|switch|case|default|break|for|while|int|float|bool|auto|const|extern|reinterpret_cast|static_cast|nullptr|true|false|u8|u32|s32|f32|class|struct)\b'
        self.fmt, self.kw = fmt, kw; self.restyle(False)

    def restyle(self, redo=True):
        fmt = self.fmt
        self.rules = [(re.compile(r'\b(0x[0-9a-fA-F]+|\d+\.?\d*f?)\b'), fmt(C['code_num'])), (re.compile(self.kw), fmt(C['code_kw'], True)), (re.compile(r'^\s*#\w+'), fmt(C['code_pp'])),
                      (re.compile(r'"[^"]*"'), fmt(C['code_str'])), (re.compile(r'//.*|/\*.*?\*/'), fmt(C['code_cm']))]
        if redo: self.rehighlight()

    def highlightBlock(self, text):
        for rx, f in self.rules:
            for m in rx.finditer(text): self.setFormat(m.start(), m.end() - m.start(), f)


# ---------------- block palette ----------------
class DragTree(QTreeWidget):
    def mimeData(self, items):
        m = QMimeData(); m.setText(items[0].data(0, Qt.UserRole) or ''); return m


class Palette(QWidget):
    add_pre = Signal(str)  # palette name
    add_lib = Signal(str)  # path of a saved function (.odnf)
    browse = Signal()      # open the game function browser
    plugfn = Signal()      # open the plugin function browser

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(8, 8, 8, 8); v.setSpacing(8)
        self.btn = QPushButton('  Game function…'); bind(self.btn, 'plus', '#ffffff'); self.btn.setObjectName('pri'); self.btn.setToolTip('Search the game for a function to call or hook (Ctrl+Shift+F)'); v.addWidget(self.btn)
        self.btn2 = QPushButton('  Plugin function…'); bind(self.btn2, 'func'); self.btn2.setToolTip('Functions added by plugins, such as Dear ImGui (Ctrl+Shift+K)'); self.btn2.clicked.connect(self.plugfn.emit); v.addWidget(self.btn2)
        hint = QLabel('Call or hook any function of Super Mario Odyssey.'); hint.setWordWrap(True); hint.setStyleSheet('color:#8a91a5'); v.addWidget(hint)
        self.filter = QLineEdit(); self.filter.setPlaceholderText('Filter blocks…'); self.filter.setClearButtonEnabled(True); v.addWidget(self.filter)
        self.tree = DragTree(); self.tree.setHeaderHidden(True); self.tree.setDragEnabled(True); v.addWidget(self.tree, 1)
        tip = QLabel('Double-click or drag a block onto the canvas.'); tip.setWordWrap(True); tip.setStyleSheet('color:#8a91a5'); v.addWidget(tip)
        self.lib = None; self.rebuild()
        self.btn.clicked.connect(self.browse.emit); self.filter.textChanged.connect(self._filter)
        self.tree.itemDoubleClicked.connect(self._double)

    def rebuild(self):
        """(Re)build the block tree from GRP (built-in blocks + plugin nodes), keeping the library section."""
        self.tree.clear(); self.btn2.setVisible(bool(PN.CATALOG)) if hasattr(self, 'btn2') else None
        for g, items in GRP.items():
            top = QTreeWidgetItem([g]); top.setFlags(Qt.ItemIsEnabled); self.tree.addTopLevelItem(top)
            for k in items:
                c = QTreeWidgetItem([k]); c.setData(0, Qt.UserRole, 'odn:pre:' + k); c.setToolTip(0, PRE[k][3]); top.addChild(c)
        self.lib = QTreeWidgetItem(['My library']); self.lib.setFlags(Qt.ItemIsEnabled); self.tree.addTopLevelItem(self.lib); self.tree.expandAll()
        self._filter(self.filter.text())

    def _double(self, it, _=0):
        v = it.data(0, Qt.UserRole) or ''
        if v.startswith('odn:pre:'): self.add_pre.emit(v[8:])
        elif v.startswith('odn:lib:'): self.add_lib.emit(v[8:])

    def set_library(self, entries):
        """entries: [(path, name, description, node count)]"""
        while self.lib.childCount(): self.lib.removeChild(self.lib.child(0))
        for p, name, desc, n in entries:
            c = QTreeWidgetItem([name]); c.setData(0, Qt.UserRole, f'odn:lib:{p}'); c.setToolTip(0, (desc + '\n' if desc else '') + tr('{0} nodes - double-click or drag to insert', n)); self.lib.addChild(c)
        if not entries:
            c = QTreeWidgetItem(['(empty: save a function with Library > Save selection)']); c.setFlags(Qt.NoItemFlags); self.lib.addChild(c)
        self.lib.setExpanded(True)

    def _filter(self, text):
        q = text.lower().strip()
        for i in range(self.tree.topLevelItemCount()):
            top, any_ = self.tree.topLevelItem(i), False
            for j in range(top.childCount()):
                c = top.child(j); key = (c.data(0, Qt.UserRole) or '')[8:] if str(c.data(0, Qt.UserRole) or '').startswith('odn:pre:') else ''; hide = bool(q) and q not in c.text(0).lower() and q not in key.lower() and q not in (c.toolTip(0) or '').lower(); c.setHidden(hide); any_ |= not hide
            top.setHidden(not any_)


# ---------------- list editor: one small box per item, with a + button ----------------
class ListEditor(QWidget):
    """Edits a comma separated list as boxes: 'params' = type + name, 'types' = type, 'cases' = value."""
    changed = Signal(str)
    NOUN = dict(params='argument', types='argument', cases='case')

    def __init__(self, kind, text):
        super().__init__(); self.kind, self.rows = kind, []
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(6); self.box = QVBoxLayout(); self.box.setSpacing(6); v.addLayout(self.box)
        self.btn = QPushButton('  Add ' + self.NOUN[kind]); bind(self.btn, 'plus', size=16); self.btn.clicked.connect(self._new); v.addWidget(self.btn)
        for item in self._parse(text): self._row(item)
        self._label()

    def _parse(self, text):
        if self.kind == 'params': return [(t, n) for n, t in parse_params(text)]
        return [(x,) for x in split_top(text)]

    def _combo(self, text):
        w = QComboBox(); w.setEditable(True); w.addItems(COMMON_TYPES); w.setEditText(text); w.setInsertPolicy(QComboBox.NoInsert); w.setMinimumWidth(110)
        w.currentTextChanged.connect(lambda _: self._emit()); return w

    def _row(self, item):
        fr = QFrame(); fr.setObjectName('row'); h = QHBoxLayout(fr); h.setContentsMargins(8, 6, 6, 6); h.setSpacing(6)
        num = QLabel(); num.setStyleSheet('color:#8a91a5'); num.setMinimumWidth(52); h.addWidget(num); ws = []
        if self.kind == 'cases':
            e = QLineEdit(item[0]); e.setPlaceholderText('value, e.g. 0'); e.textEdited.connect(lambda _: self._emit()); h.addWidget(e, 1); ws.append(e)
        else:
            c = self._combo(item[0]); h.addWidget(c, 3); ws.append(c)
            if self.kind == 'params':
                e = QLineEdit(item[1]); e.setPlaceholderText('name'); e.textEdited.connect(lambda _: self._emit()); h.addWidget(e, 2); ws.append(e)
        x = QToolButton(); bind(x, 'x', size=14); x.setToolTip('Remove'); x.clicked.connect(lambda _=False, fr=fr: self._remove(fr)); h.addWidget(x)
        self.box.addWidget(fr); self.rows.append((fr, num, ws))

    def _label(self):
        for i, (fr, num, ws) in enumerate(self.rows): num.setText(f'{"case" if self.kind == "cases" else "arg"} {i + 1}')

    def _new(self):
        if self.kind == 'cases':
            nums = [int(w[2][0].text()) for w in self.rows if w[2][0].text().strip().lstrip('-').isdigit()]; self._row((str(max(nums) + 1 if nums else 0),))
        elif self.kind == 'params': self._row(('int', f'arg{len(self.rows) + 1}'))
        else: self._row(('int',))
        self._label(); self._emit()

    def _remove(self, fr):
        self.rows = [r for r in self.rows if r[0] is not fr]; self.box.removeWidget(fr); fr.setParent(None); fr.deleteLater(); self._label(); self._emit()

    def value(self):
        out = []
        for i, (fr, num, ws) in enumerate(self.rows):
            first = ws[0].currentText().strip() if self.kind != 'cases' else ws[0].text().strip()
            if self.kind == 'params': out.append(f"{first or 'int'} {ws[1].text().strip() or f'arg{i + 1}'}")
            elif self.kind == 'types': out.append(first or 'int')
            elif first: out.append(first)
        return ', '.join(out)

    def _emit(self): self.changed.emit(self.value())


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
        adv = []
        for fd in fields_for(n):
            if fd.key in ('save', 'inline') and n.type in ('callgame', 'callfn', 'callext') and self.graph.ret_type(n) == 'void': continue  # nothing to save / use as a value
            if fd.key == 'inline' and n.type in CALLS: continue  # now a right-click option on the node
            if fd.key in ADV_KEYS and n.type in ('local', 'global'): adv.append(fd); continue
            self.set_form.addRow(fd.label, self._field(n, fd))
        if adv:  # qualifiers and arrays: a collapsed "Advanced" section (open by itself when the node already uses them)
            used = any(n.f.get(fd.key) for fd in adv); box = QWidget(); bf = QFormLayout(box); bf.setContentsMargins(0, 0, 0, 0)
            for fd in adv:
                if fd.key == 'ainit' and not n.f.get('array'): continue
                bf.addRow(fd.label, self._field(n, fd))
            tg = QToolButton(); tg.setText('Advanced (constexpr, arrays…)'); tg.setCheckable(True); tg.setChecked(used); tg.setArrowType(Qt.DownArrow if used else Qt.RightArrow); tg.setToolButtonStyle(Qt.ToolButtonTextBesideIcon); tg.setAutoRaise(True)
            box.setVisible(used); tg.toggled.connect(lambda on: (box.setVisible(on), tg.setArrowType(Qt.DownArrow if on else Qt.RightArrow)))
            self.set_form.addRow(tg); self.set_form.addRow(box)
        self.refresh()

    def _field(self, n, fd):
        val = n.f.get(fd.key, '')
        if n.type == 'literal' and fd.key == 'value' and n.f.get('type', '').strip() == 'bool':  # a bool constant is a check box, not a text prompt
            w = QCheckBox('true  (unchecked = false)'); w.setChecked(str(val).strip().lower() == 'true'); w.toggled.connect(lambda b: self._set('value', 'true' if b else 'false')); return w
        if fd.kind == 'choice':
            w = QComboBox()
            for key, lab in fd.opts: w.addItem(lab, key)
            w.setCurrentIndex(max(0, w.findData(val))); w.currentIndexChanged.connect(lambda _, w=w, k=fd.key: self._set(k, w.currentData())); return w
        if fd.kind == 'bool':
            w = QCheckBox(); w.setChecked(bool(val)); w.toggled.connect(lambda b, k=fd.key: self._set(k, b)); return w
        if fd.kind in ('params', 'types', 'cases'):
            w = ListEditor(fd.kind, str(val)); w.changed.connect(lambda t, k=fd.key: self._set(k, t)); return w
        if fd.kind == 'rtype':
            w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0); lab = QLabel(); b1, b2 = QPushButton('Change…'), QPushButton('Reset')
            b1.setToolTip('The catalog guesses return types from headers; change it if a function marked void really returns something'); b2.setToolTip('Back to the catalog type')
            def upd():
                g, nn = self.graph, self.graph.nodes.get(self.nid)
                if nn: eff, cat = g.ret_type(nn), g.sg(nn)['r']; lab.setText(f'<b>{escape(eff)}</b>' + (tr(' <span style="color:#e6b673">(catalog: {0})</span>', escape(cat)) if eff != cat else ''))
            def change():
                nn = self.graph.nodes.get(self.nid)
                if not nn: return
                r = ask_ret_type(self, self.graph, nn.f.get('sym'), self.graph.ret_type(nn))
                if r:
                    t, rem = r; cat = self.graph.sg(nn)['r']
                    if rem: remember(self.graph, nn.f['sym'], t if t != cat else ''); nn.f['rtype'] = ''
                    else: nn.f['rtype'] = t if t != cat else ''
                    self.changed.emit(); self.show_node(self.nid)
            def reset():
                nn = self.graph.nodes.get(self.nid)
                if nn: nn.f['rtype'] = ''; remember(self.graph, nn.f.get('sym'), ''); self.changed.emit(); self.show_node(self.nid)
            b1.clicked.connect(change); b2.clicked.connect(reset); h.addWidget(lab, 1); h.addWidget(b1); h.addWidget(b2); upd(); return w
        if fd.kind == 'qual':
            w = QComboBox(); w.setEditable(True); w.addItems(QUALS); w.setEditText(str(val)); w.setInsertPolicy(QComboBox.NoInsert); w.currentTextChanged.connect(lambda t, k=fd.key: self._set(k, t.strip())); return w
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
            c = g.sg(n); known = n.f.get('sym') in g.cat; rt = g.ret_type(n) if n.type == 'callgame' else (n.f.get('ret') or c['r'])
            self.f_sig.setText(f"{rt} {c['n']}({', '.join(c['p'])})" if known else 'Symbol not found in the catalog'); self.f_ret.setText((rt + (tr('   (catalog: {0})', c['r']) if rt != c['r'] else '')) if known else '?')
            self.f_off.setText(f"0x{c['o']:x}" if known else '?'); self.f_sym.setText(n.f.get('sym', '')); self.f_sym.setCursorPosition(0)
            self.f_status.setText(('Matching (decompiled)' if c['st'] == 'M' else 'Not matching / not decompiled yet') if known else '?')
        self.set_box.setVisible(self.set_form.rowCount() > 0)
        self._clear(self.in_form); self._clear(self.out_form)
        hint = QLabel('Connect a node, or type a fixed value.'); hint.setStyleSheet('color:#8a91a5'); hint.setWordWrap(True); self.in_form.addRow(hint)
        for p in ins:
            if p.type == E: continue
            lab = QLabel(tr('<b>{0}</b><br><span style="color:#8a91a5">{1}</span>', escape(p.label), escape(p.type or 'any type')))
            if g.linked(n.id, p.id, 'i'):
                w = QLabel('connected to another node'); w.setStyleSheet('color:#8a91a5;font-style:italic')
            else: w = make_editor(p.type, n.d.get(p.id, ''), lambda raw, pid=p.id: self._dflt(pid, raw))
            self.in_form.addRow(lab, w)
        for p in outs:
            if p.type == E: continue
            self.out_form.addRow(QLabel(f'<b>{escape(p.label)}</b>'), QLabel(tr('<span style="color:#8a91a5">{0}</span>', escape(p.type or 'any type'))))
        self.in_box.setVisible(self.in_form.rowCount() > 1); self.out_box.setVisible(self.out_form.rowCount() > 0)
        self.out_box.setTitle('Outputs' + ('  (values the game gives to your hook)' if n.type == 'hook' else ''))

    def _set(self, k, v):
        n = self.graph.nodes.get(self.nid)
        if n and n.f.get(k) != v:
            was = n.f.get(k); n.f[k] = v
            if k == 'array' and n.type in ('local', 'global') and bool(was) != bool(v): QTimer.singleShot(0, lambda nid=n.id: self.show_node(nid) if self.nid == nid else None)
            if n.type == 'literal' and k == 'type':  # keep the value valid for the new type, and redraw the form (bool shows a check box)
                cur = str(n.f.get('value', '')).strip().lower()
                if v.strip() == 'bool' and cur not in ('true', 'false'): n.f['value'] = 'false'
                elif v.strip() != 'bool' and cur in ('true', 'false'): n.f['value'] = '0'
                QTimer.singleShot(0, lambda nid=n.id: self.show_node(nid) if self.nid == nid else None)
            self.changed.emit()

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

    def start(self, cmd, cwd, env='', distro=''):
        if self.p: return
        self.p = QProcess(self); self.p.setProcessChannelMode(QProcess.MergedChannels)
        prog, args, native = invocation(env, distro, cmd, cwd)
        if cwd and env != 'wsl' and os.path.isdir(cwd): self.p.setWorkingDirectory(cwd)  # for WSL the folder is passed with --cd
        self.p.setProgram(prog); self.p.setArguments(args)
        if native and hasattr(self.p, 'setNativeArguments'): self.p.setNativeArguments(native)
        self.p.readyRead.connect(lambda: self.output.emit(bytes(self.p.readAll()).decode('utf-8', 'replace')))
        self.p.errorOccurred.connect(self._err); self.p.finished.connect(self._fin); self.p.start()

    def _err(self, e):
        if e == QProcess.FailedToStart: self.output.emit('Could not start the command (is WSL installed and the distro name right? Check Settings > Build environment).\n'); self._fin(1)

    def _fin(self, code, *_):
        if self.p: p, self.p = self.p, None; p.deleteLater(); self.done.emit(int(code))

    def stop(self):
        if self.p: self.p.kill()
