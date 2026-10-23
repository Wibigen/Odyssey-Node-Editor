"""Work area: nodes, links, zoom/pan, drag & drop (Qt Graphics View)."""
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap, QFont, QFontMetricsF, QPainter, QPainterPath, QPainterPathStroker, QPen, QPolygonF, QTransform
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsScene, QGraphicsView, QMenu

from .graph import CALLS, COLOR_NAMES, E
from .theme import C, HEAD_COLORS, pin_color

HEAD, ROW, SUB, SAVEH = 28, 22, 20, 24
ZOOM_MIN, ZOOM_MAX = 0.03, 6.0
CH = 17  # header height of the small Math & logic nodes
F_TITLE, F_PIN, F_SUB = QFont(), QFont(), QFont('Consolas')
F_TITLE.setBold(True); F_TITLE.setPointSizeF(9.5); F_PIN.setPointSizeF(8.5); F_SUB.setPointSizeF(8.5)
FM_T, FM_P = QFontMetricsF(F_TITLE), QFontMetricsF(F_PIN)


def head_color(n):
    if n.type == 'plug':
        from .plugnodes import plug_def; d = plug_def(n.f.get('pid')); return (d or {}).get('color') or '#8a6fd1'
    return HEAD_COLORS.get(n.type, '#6b7385')


COMPACT = ('op', 'cmp', 'logic', 'not')  # Math & logic nodes are drawn small and square


def swatch(hex_):
    pm = QPixmap(16, 16); pm.fill(QColor(hex_)); return QIcon(pm)


def short(v, n=26):
    v = str(v).replace('\n', ' '); return v if len(v) <= n else v[:n - 1] + '…'


class NodeItem(QGraphicsItem):
    def __init__(self, scn, node):
        super().__init__()
        self.scn, self.node, g = scn, node, scn.graph
        self.title, self.ins, self.outs = g.spec(node); self.sub = g.subtitle(node)
        self.texts = {}  # (direction, pin id) -> (label, fixed value shown after the label)
        for d, lst in (('i', self.ins), ('o', self.outs)):
            for p in lst:
                v = '' if d == 'o' or p.type == E or g.linked(node.id, p.id, 'i') else str(node.d.get(p.id, '')).strip()
                self.texts[d, p.id] = (p.label, ('= ' + short(v)) if v else '')
        wl = max([FM_P.horizontalAdvance(a + ('  ' + b if b else '')) for (d, _), (a, b) in self.texts.items() if d == 'i'] or [0])
        wr = max([FM_P.horizontalAdvance(a) for (d, _), (a, b) in self.texts.items() if d == 'o'] or [0])
        self.compact = node.type in COMPACT
        self.w = max(190.0, wl + wr + 56, min(FM_T.horizontalAdvance(self.title) + 28, 360.0))
        f = node.f; self.saved = f.get('save') if (node.type in CALLS or g.has_inline(node)) and not f.get('inline') and g.ret_type(node) != 'void' else ''  # a call that keeps its result in a variable
        self.y0 = HEAD + (SUB if self.sub else 0) + (SAVEH if self.saved else 0) + 8
        self.h = self.y0 + max(len(self.ins), len(self.outs), 1) * ROW + 6
        if self.compact: self.w = self.h = 66.0
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True); self.setZValue(1); self.setPos(node.x, node.y); self.setToolTip(self.title + ('' if not self.compact else '  (' + self.sub + ')' if self.sub else ''))

    def boundingRect(self): return QRectF(-14, -6, self.w + 28, self.h + 12)
    def shape(self):
        p = QPainterPath(); p.addRect(self.boundingRect()); return p

    def pin_pos(self, d, k):
        if self.compact: n = len(self.ins if d == 'i' else self.outs); return QPointF(0 if d == 'i' else self.w, CH + (self.h - CH) * (k + 1) / (n + 1))
        return QPointF(0 if d == 'i' else self.w, self.y0 + k * ROW + ROW / 2)
    def pin_index(self, d, pid): return next(i for i, p in enumerate(self.ins if d == 'i' else self.outs) if p.id == pid)

    def pin_at(self, pos):
        best = None
        for d, lst in (('i', self.ins), ('o', self.outs)):
            for k, p in enumerate(lst):
                dist = (self.pin_pos(d, k) - pos).manhattanLength()
                if dist <= 18 and (best is None or dist < best[0]): best = (dist, p.id, d)
        return best[1:] if best else None

    KIND = {'op': 'Math', 'cmp': 'Compare', 'logic': 'Logic', 'not': 'Logic'}
    SYMS = {'&&': 'AND', '||': 'OR', '==': '=', '!=': '≠', '<=': '≤', '>=': '≥'}  # conditions read as words / math signs, not as C++

    def paint_compact(self, p):
        W, H = self.w, self.h; n = self.node; col = QColor(head_color(n))
        body = QPainterPath(); body.addRoundedRect(QRectF(0, 0, W, H), 10, 10); p.fillPath(body, QColor(C['node']))
        p.save(); p.setClipPath(body); p.fillRect(QRectF(0, 0, W, CH), col); p.restore()
        sel = self.isSelected(); p.setPen(QPen(QColor(C['ac']) if sel else QColor(C['ln']), 2.2 if sel else 1.4)); p.setBrush(Qt.NoBrush); p.drawPath(body)
        f = QFont(F_TITLE); f.setPointSizeF(8); p.setFont(f); p.setPen(Qt.white); p.drawText(QRectF(8, 0, W - 16, CH), Qt.AlignVCenter | Qt.AlignLeft, self.KIND.get(n.type, self.title))
        raw = 'NOT' if n.type == 'not' else str(n.f.get('op', '?')); sym = self.SYMS.get(raw, raw) if n.type != 'op' else raw
        f = QFont(F_TITLE); f.setPointSizeF(15 if len(sym) < 3 else 9.5); p.setFont(f); p.setPen(Qt.white)
        p.drawText(QRectF(26, CH, W - 36, H - CH - (12 if n.type in ('op', 'cmp') else 0)), Qt.AlignCenter, sym)
        if n.type in ('op', 'cmp'): p.setFont(F_SUB); p.setPen(QColor(C['mu'])); p.drawText(QRectF(24, H - 15, W - 34, 13), Qt.AlignCenter, str(n.f.get('type', '')))
        p.setFont(F_SUB)
        for k, pin in enumerate(self.ins):
            pt = self.pin_pos('i', k); linked = self.scn.graph.linked(n.id, pin.id, 'i'); c = QColor(pin_color(pin.type))
            p.setPen(QPen(c, 2)); p.setBrush(c if linked else QColor(C['node'])); p.drawEllipse(pt, 5, 5)
            v = '' if linked else str(n.d.get(pin.id, '')).strip()
            p.setPen(QColor(C['val']) if v else QColor(C['mu'])); p.drawText(QRectF(pt.x() + 8, pt.y() - 9, 20, 18), Qt.AlignVCenter | Qt.AlignLeft, short(v, 4) if v else pin.label[:1])
        for k, pin in enumerate(self.outs):
            pt = self.pin_pos('o', k); c = QColor(pin_color(pin.type)); p.setPen(QPen(c, 2)); p.setBrush(c if self.scn.graph.linked(n.id, pin.id, 'o') else QColor(C['node'])); p.drawEllipse(pt, 5, 5)

    def paint(self, p, opt, widget=None):
        p.setRenderHint(QPainter.Antialiasing); W = self.w
        if self.compact: return self.paint_compact(p)
        body = QPainterPath(); body.addRoundedRect(QRectF(0, 0, W, self.h), 10, 10)
        plug = self.node.type == 'plug'; pc = QColor(head_color(self.node))
        if plug:  # a soft halo in the plugin's color: plugin nodes are easy to tell apart without shouting
            p.setPen(Qt.NoPen)
            for grow, alpha in ((6.0, 10), (4.0, 16), (2.2, 26)):
                halo = QColor(pc); halo.setAlpha(alpha); p.setBrush(halo); p.drawRoundedRect(QRectF(0, 0, W, self.h).adjusted(-grow, -grow, grow, grow), 10 + grow, 10 + grow)
        p.fillPath(body, QColor(C['node']))
        p.save(); p.setClipPath(body); p.fillRect(QRectF(0, 0, W, HEAD), QColor(head_color(self.node))); p.restore()
        sel = self.isSelected(); edge = QColor(pc.red(), pc.green(), pc.blue(), 190) if plug else QColor(C['ln']); p.setPen(QPen(QColor(C['ac']) if sel else edge, 2.2 if sel else 1.4)); p.setBrush(Qt.NoBrush); p.drawPath(body)
        p.setFont(F_TITLE); p.setPen(Qt.white)
        p.drawText(QRectF(10, 0, W - 20, HEAD), Qt.AlignVCenter | Qt.AlignLeft, FM_T.elidedText(self.title, Qt.ElideRight, W - 20))
        if self.sub:
            p.setFont(F_SUB); p.setPen(QColor(C['sub'])); p.drawText(QRectF(10, HEAD + 1, W - 20, SUB), Qt.AlignVCenter | Qt.AlignLeft, QFontMetricsF(F_SUB).elidedText(self.sub, Qt.ElideRight, W - 20))
        if self.saved:  # the variable that receives the result, clearly readable
            y = HEAD + (SUB if self.sub else 0) + 2; r = QRectF(10, y, W - 20, SAVEH - 4); p.setPen(QPen(QColor('#f0b429'), 1.2)); p.setBrush(QColor(240, 180, 41, 38)); p.drawRoundedRect(r, 6, 6)
            f = QFont(F_TITLE); f.setPointSizeF(9.5); p.setFont(f); p.setPen(QColor(C['warn'])); p.drawText(r.adjusted(8, 0, -8, 0), Qt.AlignVCenter | Qt.AlignLeft, QFontMetricsF(f).elidedText('Saved in  ' + self.saved, Qt.ElideRight, W - 36))
        p.setFont(F_PIN)
        for d, lst in (('i', self.ins), ('o', self.outs)):
            for k, pin in enumerate(lst):
                c, pt = QColor(pin_color(pin.type)), self.pin_pos(d, k); linked = self.scn.graph.linked(self.node.id, pin.id, d)
                if pin.type == E:  # execution pin: arrow shape
                    p.setBrush(QColor(C['tx']) if linked else QColor(C['node'])); p.setPen(QPen(QColor(C['tx']), 1.8))
                    p.drawPolygon(QPolygonF([pt + QPointF(-5, -6), pt + QPointF(3, -6), pt + QPointF(7, 0), pt + QPointF(3, 6), pt + QPointF(-5, 6)]))
                else:
                    p.setPen(QPen(c, 2)); p.setBrush(c if linked else QColor(C['node'])); p.drawEllipse(pt, 5.5, 5.5)
                label, val = self.texts[d, pin.id]
                if d == 'i':
                    p.setPen(QColor(C['mu'])); p.drawText(QRectF(pt.x() + 12, pt.y() - 10, W, 20), Qt.AlignVCenter | Qt.AlignLeft, label)
                    if val: p.setPen(QColor(C['val'])); p.drawText(QRectF(pt.x() + 12 + FM_P.horizontalAdvance(label) + 8, pt.y() - 10, W, 20), Qt.AlignVCenter | Qt.AlignLeft, val)
                else: p.setPen(QColor(C['mu'])); p.drawText(QRectF(pt.x() - W - 12, pt.y() - 10, W, 20), Qt.AlignVCenter | Qt.AlignRight, label)

    def hoverMoveEvent(self, ev):
        hit = self.pin_at(ev.pos())
        if hit:
            pin = next(p for p in (self.ins if hit[1] == 'i' else self.outs) if p.id == hit[0])
            fixed = self.node.d.get(pin.id, '') if hit[1] == 'i' and not self.scn.graph.linked(self.node.id, pin.id, 'i') else ''
            self.setToolTip(f"{pin.label or 'execution'}: " + ('execution flow' if pin.type == E else (pin.type or 'any type')) + (f'\nfixed value: {fixed}' if fixed else ''))
        else: self.setToolTip(self.title)
        super().hoverMoveEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        if not self.pin_at(ev.pos()): self.scn.node_activated.emit(self.node.id)
        ev.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scn.snap and self.scn.mouseGrabberItem() is self:
            g = self.scn.grid; return QPointF(round(value.x() / g) * g, round(value.y() / g) * g)
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.node.x, self.node.y = value.x(), value.y(); self.scn.update_edges(); self.scn.moved.emit()
        return super().itemChange(change, value)


class GroupItem(QGraphicsItem):
    """A frame around some nodes (organisation only). Drag its title bar to move all of them."""
    PAD, HEADH = 24, 30

    def __init__(self, scn, gid):
        super().__init__(); self.scn, self.gid = scn, gid; self._r = QRectF(0, 0, 10, 10); self._last = None
        self.setFlags(QGraphicsItem.ItemIsSelectable); self.setZValue(-2); self.setAcceptHoverEvents(True); self.setCursor(Qt.OpenHandCursor); self.refresh()

    def data_(self): return self.scn.graph.groups.get(self.gid, {})
    def members(self): return [self.scn.node_items[i] for i in self.data_().get('nodes', []) if i in self.scn.node_items]

    def refresh(self):
        m = self.members()
        if not m: return
        r = QRectF(m[0].x(), m[0].y(), m[0].w, m[0].h)
        for it in m[1:]: r = r.united(QRectF(it.x(), it.y(), it.w, it.h))
        r = r.adjusted(-self.PAD, -self.PAD - self.HEADH, self.PAD, self.PAD)
        if r != self._r: self.prepareGeometryChange(); self._r = r

    def boundingRect(self): return self._r.adjusted(-3, -3, 3, 3)
    def head(self): return QRectF(self._r.left(), self._r.top(), self._r.width(), self.HEADH)
    def shape(self):
        p = QPainterPath(); p.addRect(self.head()); return p

    def paint(self, p, opt, widget=None):
        d = self.data_(); col = QColor(d.get('color', '#3a7bd5')); r = self._r; p.setRenderHint(QPainter.Antialiasing)
        body = QPainterPath(); body.addRoundedRect(r, 14, 14); f = QColor(col); f.setAlpha(30); p.fillPath(body, f)
        p.save(); p.setClipPath(body); h = QColor(col); h.setAlpha(150 if self.isSelected() else 110); p.fillRect(self.head(), h); p.restore()
        b = QColor(col); b.setAlpha(230 if self.isSelected() else 150); p.setPen(QPen(b, 2.6 if self.isSelected() else 1.6)); p.setBrush(Qt.NoBrush); p.drawPath(body)
        p.setFont(F_TITLE); p.setPen(Qt.white); n = len(d.get('nodes', []))
        p.drawText(self.head().adjusted(12, 0, -12, 0), Qt.AlignVCenter | Qt.AlignLeft, FM_T.elidedText(d.get('name', 'Group'), Qt.ElideRight, r.width() - 90))
        p.setFont(F_PIN); p.setPen(QColor(255, 255, 255, 170)); p.drawText(self.head().adjusted(12, 0, -12, 0), Qt.AlignVCenter | Qt.AlignRight, f'{n} node{"s" if n != 1 else ""}')

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton: self._last = ev.scenePos(); self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._last is not None and ev.buttons() & Qt.LeftButton:
            d = ev.scenePos() - self._last; self._last = ev.scenePos()
            for it in self.members(): it.setPos(it.pos() + d)
            ev.accept(); return
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev): self._last = None; self.setCursor(Qt.OpenHandCursor); super().mouseReleaseEvent(ev)
    def mouseDoubleClickEvent(self, ev): self.scn.group_edit.emit(self.gid); ev.accept()


class NoteItem(QGraphicsItem):
    """A free comment on the canvas (never part of the generated code)."""
    W = 280

    def __init__(self, scn, nid):
        super().__init__(); self.scn, self.nid = scn, nid; d = scn.graph.notes[nid]; self.text = d.get('text', '')
        self.rect = FM_P.boundingRect(QRectF(0, 0, self.W - 28, 10000), Qt.TextWordWrap, self.text or ' ').adjusted(0, 0, 0, 0)
        self.h = max(46.0, self.rect.height() + 26)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges); self.setZValue(-1); self.setPos(d['x'], d['y'])
        self.setToolTip('Comment (double-click to edit)')

    def boundingRect(self): return QRectF(-3, -3, self.W + 6, self.h + 6)

    def paint(self, p, opt, widget=None):
        col = QColor(self.scn.graph.notes.get(self.nid, {}).get('color', '#c98a2b')); p.setRenderHint(QPainter.Antialiasing)
        body = QPainterPath(); body.addRoundedRect(QRectF(0, 0, self.W, self.h), 8, 8); f = QColor(col); f.setAlpha(60); p.fillPath(body, f)
        p.save(); p.setClipPath(body); p.fillRect(QRectF(0, 0, 6, self.h), col); p.restore()
        p.setPen(QPen(col if self.isSelected() else QColor(col.red(), col.green(), col.blue(), 140), 2.4 if self.isSelected() else 1.2)); p.setBrush(Qt.NoBrush); p.drawPath(body)
        p.setFont(F_PIN); p.setPen(QColor('#f3efe6')); p.drawText(QRectF(16, 12, self.W - 28, self.h - 20), Qt.TextWordWrap, self.text)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged and self.nid in self.scn.graph.notes:
            d = self.scn.graph.notes[self.nid]; d['x'], d['y'] = value.x(), value.y(); self.scn.moved.emit()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, ev): self.scn.note_edit.emit(self.nid); ev.accept()


def bezier(a, b):
    dx = max(60.0, abs(b.x() - a.x()) * 0.5); p = QPainterPath(a); p.cubicTo(a + QPointF(dx, 0), b - QPointF(dx, 0), b); return p


class EdgeItem(QGraphicsPathItem):
    def __init__(self, scn, edge):
        super().__init__()
        self.scn, self.edge = scn, edge
        self.setFlags(QGraphicsItem.ItemIsSelectable); self.setZValue(0); self.setAcceptHoverEvents(True)
        t = scn.graph.pin_type(edge[0][0], edge[0][1], 'o'); self.ex = t == E; self.col = QColor(C['tx'] if self.ex else pin_color(t))
        self.update_path()

    def update_path(self):
        a, b = self.scn.node_items.get(self.edge[0][0]), self.scn.node_items.get(self.edge[1][0])
        if not a or not b: return
        pa = a.pos() + a.pin_pos('o', a.pin_index('o', self.edge[0][1])); pb = b.pos() + b.pin_pos('i', b.pin_index('i', self.edge[1][1]))
        self.prepareGeometryChange(); self.setPath(bezier(pa, pb))

    def shape(self):
        s = QPainterPathStroker(); s.setWidth(14); return s.createStroke(self.path())

    def paint(self, p, opt, widget=None):
        p.setRenderHint(QPainter.Antialiasing); sel = self.isSelected()
        p.setPen(QPen(QColor(C['ac']) if sel else self.col, (3.4 if self.ex else 2.4) + (1 if sel else 0))); p.setBrush(Qt.NoBrush); p.drawPath(self.path())

    def mouseDoubleClickEvent(self, ev): self.scn.remove_edge(self.edge)


class GraphScene(QGraphicsScene):
    changed = Signal()           # structure or values changed
    moved = Signal()             # a node was moved
    picked = Signal(int)         # selected node id (0 = none / several)
    node_activated = Signal(int)  # double-click on a node
    empty_double = Signal(QPointF)
    empty_menu = Signal(QPointF, QPoint)
    group_edit = Signal(int)     # double-click on a group title
    note_edit = Signal(int)      # double-click on a comment
    link_dropped = Signal(int, str, str, QPointF, QPoint)  # a link was released on empty space: (node id, pin id, 'i'|'o', scene pos, screen pos)
    find_request = Signal(str)   # 'Find in the graph' from a context menu (text to look for)
    request = Signal(str, int)   # context menu actions handled by the window: 'group', 'ungroup', 'rename_group', 'select_group', ...

    def __init__(self, graph):
        super().__init__(); self.graph = graph; self.node_items, self.edge_items, self.group_items, self.note_items = {}, [], {}, {}; self._link = None; self._temp = None; self._lock = False; self.snap, self.grid, self.links_top, self.autogroup, self._dragged = False, 24, False, True, False
        self.search = ''; self.dropmenu = True
        self.setSceneRect(-30000, -30000, 60000, 60000); self.selectionChanged.connect(self._sel); self.moved.connect(lambda: setattr(self, '_dragged', True))

    def _sel(self):
        if self._lock: return
        ids = self.selected_ids(); self.picked.emit(ids[0] if len(ids) == 1 else 0); self.apply_z()

    def apply_z(self):
        """Option: the links of the selected nodes are drawn above everything else (nodes included)."""
        sel = set(self.selected_ids()) if self.links_top else set()
        for e in self.edge_items: e.setZValue(3 if sel and (e.edge[0][0] in sel or e.edge[1][0] in sel) else 0)

    def set_search(self, text): self.search = text.strip(); return self.apply_search()

    def apply_search(self):
        """Grey out every node (and link) that does not mention the searched text. Returns the matching ids."""
        hit = self.graph.search_ids(self.search) if self.search else None
        for i, it in self.node_items.items(): it.setOpacity(1.0 if hit is None or i in hit else 0.14)
        for e in self.edge_items: e.setOpacity(1.0 if hit is None or (e.edge[0][0] in hit and e.edge[1][0] in hit) else 0.08)
        for g in self.group_items.values(): g.setOpacity(1.0 if hit is None or any(i in hit for i in g.data_().get('nodes', [])) else 0.3)
        return hit or set()

    @staticmethod
    def search_term(n):
        f = n.f; return str(f.get('save') or f.get('variable') or (f.get('name') if n.type != 'hook' else '') or f.get('member') or f.get('tpl') or '').strip()

    def selected_ids(self): return [i.node.id for i in self.selectedItems() if isinstance(i, NodeItem)]

    def select_only(self, nid):
        self.clearSelection()
        if nid in self.node_items: self.node_items[nid].setSelected(True)

    def rebuild(self, keep=None):
        self._lock = True
        keep = set(self.selected_ids()) if keep is None else set(keep)
        self.graph.prune(); self.clear(); self.node_items, self.edge_items, self.group_items, self.note_items, self._temp = {}, [], {}, {}, None
        for n in self.graph.nodes.values():
            it = NodeItem(self, n); self.addItem(it); self.node_items[n.id] = it; it.setSelected(n.id in keep)
        for e in self.graph.edges:
            it = EdgeItem(self, e); self.addItem(it); self.edge_items.append(it)
        for gid in self.graph.groups: g = GroupItem(self, gid); self.addItem(g); self.group_items[gid] = g
        for nid in self.graph.notes: n = NoteItem(self, nid); self.addItem(n); self.note_items[nid] = n
        self._lock = False; self.apply_z(); self.apply_search()

    def update_edges(self):
        for e in self.edge_items: e.update_path()
        for g in self.group_items.values(): g.refresh()

    def commit(self, keep=None): self.rebuild(keep); self.changed.emit()

    def remove_edge(self, edge):
        self.graph.edges = [e for e in self.graph.edges if e != edge]; self.commit()

    def delete_selected(self):
        for it in self.selectedItems():
            if isinstance(it, NodeItem): self.graph.remove(it.node.id)
            elif isinstance(it, EdgeItem): self.graph.edges = [e for e in self.graph.edges if e != it.edge]
            elif isinstance(it, GroupItem): self.graph.groups.pop(it.gid, None)   # only the frame goes away, never the nodes
            elif isinstance(it, NoteItem): self.graph.notes.pop(it.nid, None)
        self.commit(keep=[])

    def duplicate_selected(self):
        new = [self.graph.duplicate(i).id for i in self.selected_ids()]
        if new: self.commit(keep=new)

    def unlink(self, nid): self.graph.edges = [e for e in self.graph.edges if nid not in (e[0][0], e[1][0])]; self.commit(keep=[nid])

    # ---- creating links with the mouse ----
    def _pin_under(self, pos):
        for it in self.items(pos):
            if isinstance(it, NodeItem):
                pin = it.pin_at(it.mapFromScene(pos))
                if pin: return it, pin
        return None

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            hit = self._pin_under(ev.scenePos())
            if hit:
                it, (pid, d) = hit; self._link = (it.node.id, pid, d, it); t = self.graph.pin_type(it.node.id, pid, d)
                self._temp = QGraphicsPathItem(); self._temp.setPen(QPen(QColor(C['tx'] if t == E else pin_color(t)), 2.4, Qt.DashLine)); self._temp.setZValue(5)
                self.addItem(self._temp); ev.accept(); return
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._link:
            nid, pid, d, it = self._link; a = it.pos() + it.pin_pos(d, it.pin_index(d, pid)); b = ev.scenePos()
            self._temp.setPath(bezier(a, b) if d == 'o' else bezier(b, a)); ev.accept(); return
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        if self._link:
            nid, pid, d, _ = self._link; self._link = None
            if self._temp: self.removeItem(self._temp); self._temp = None
            hit = self._pin_under(ev.scenePos())
            if hit and self.graph.connect((nid, pid, d), (hit[0].node.id, hit[1][0], hit[1][1])):
                if self.autogroup:  # linking two nodes also groups them: the one without a group joins the other's group
                    a, b = nid, hit[0].node.id; ga, gb = self.graph.group_of(a), self.graph.group_of(b)
                    if ga is not None and gb is None: self.graph.add_to_group(ga, [b])
                    elif gb is not None and ga is None: self.graph.add_to_group(gb, [a])
                self.commit()
            elif not hit and self.dropmenu and not any(isinstance(i, NodeItem) for i in self.items(ev.scenePos())): self.link_dropped.emit(nid, pid, d, ev.scenePos(), ev.screenPos())
            ev.accept(); return
        super().mouseReleaseEvent(ev)
        if self._dragged: self._dragged = False; self._auto_group()

    def group_under(self, nid):
        """Groups (id list) whose frame contains the center of node nid, and that the node is not in yet."""
        it = self.node_items.get(nid)
        if not it: return []
        ctr = it.pos() + QPointF(it.w / 2, it.h / 2); mine = self.graph.group_of(nid)
        return [gid for gid, g in self.group_items.items() if gid != mine and g._r.contains(ctr)]

    def _auto_group(self):
        """Option: a node dropped inside a group frame joins that group (only nodes that are not in a group yet)."""
        if not self.autogroup: return
        ids, changed = self.selected_ids(), False
        for nid in ids:
            if self.graph.group_of(nid) is None:
                gs = self.group_under(nid)
                if gs: self.graph.add_to_group(gs[-1], [nid]); changed = True
        if changed: self.commit(keep=ids)

    def mouseDoubleClickEvent(self, ev):
        if not [i for i in self.items(ev.scenePos()) if isinstance(i, (NodeItem, EdgeItem))]: self.empty_double.emit(ev.scenePos()); ev.accept(); return
        super().mouseDoubleClickEvent(ev)

    def contextMenuEvent(self, ev):
        it = next((i for i in self.items(ev.scenePos()) if isinstance(i, (NodeItem, EdgeItem, GroupItem, NoteItem))), None)
        if it is None: self.empty_menu.emit(ev.scenePos(), ev.screenPos()); ev.accept(); return
        m = QMenu()
        if isinstance(it, EdgeItem): m.addAction('Delete link', lambda: self.remove_edge(it.edge))
        elif isinstance(it, GroupItem):
            m.addAction('Edit group… (name, color, nodes)', lambda: self.group_edit.emit(it.gid)); cm = m.addMenu('Color')
            for nm, c in COLOR_NAMES.items(): cm.addAction(swatch(c), nm, lambda _=False, c=c: self._color_group(it.gid, c))
            m.addAction('Add the selected nodes to this group', lambda: self._add_sel(it.gid))
            m.addAction('Select the nodes of this group', lambda: self._select_group(it.gid)); m.addSeparator(); m.addAction('Ungroup (keeps the nodes)', lambda: self._ungroup(it.gid))
        elif isinstance(it, NoteItem):
            m.addAction('Edit comment…', lambda: self.note_edit.emit(it.nid)); cm = m.addMenu('Color')
            for nm, c in COLOR_NAMES.items(): cm.addAction(swatch(c), nm, lambda _=False, c=c: self._color_note(it.nid, c))
            m.addSeparator(); m.addAction('Delete comment', lambda: self._del_note(it.nid))
        else:
            if not it.isSelected(): self.clearSelection(); it.setSelected(True)
            m.addAction('Edit…', lambda: self.node_activated.emit(it.node.id)); m.addAction('Duplicate\tCtrl+D', self.duplicate_selected)
            if it.node.type in CALLS or self.graph.has_inline(it.node):  # hide / show the execution pins: the call then runs where its result is used
                inl = bool(it.node.f.get('inline')); ac = m.addAction('Use as a value (hide execution pins)'); ac.setCheckable(True); ac.setChecked(inl)
                if not inl and self.graph.ret_type(it.node) == 'void' and it.node.type in ('callfn', 'callorig'): ac.setEnabled(False); ac.setToolTip('This call returns void, so it has no value to use')
                elif not inl and self.graph.ret_type(it.node) == 'void': ac.setToolTip('The catalog says void: the return type becomes "auto" (change it in the inspector if you know it)')
                ac.triggered.connect(lambda _=False, n=it.node: self._toggle_inline(n))
            m.addAction('Find in the graph…\tCtrl+F', lambda: self.find_request.emit(self.search_term(it.node)))
            m.addAction('Group selected nodes\tCtrl+G', lambda: self.request.emit('group', 0))
            for gid in self.group_under(it.node.id): m.addAction(swatch(self.graph.groups[gid].get('color', '#3a7bd5')), f'Put into the group "{self.graph.groups[gid].get("name", "Group")}"', lambda _=False, gid=gid: self._add_sel(gid))
            if self.graph.groups:
                am = m.addMenu('Add to group')
                for gid, gv in self.graph.groups.items(): am.addAction(swatch(gv.get('color', '#3a7bd5')), gv.get('name', 'Group'), lambda _=False, gid=gid: self._add_sel(gid))
            if self.graph.group_of(it.node.id): m.addAction('Remove from its group', lambda: self._leave_group(it.node.id))
            m.addAction('Disconnect all links', lambda: self.unlink(it.node.id)); m.addSeparator(); m.addAction('Delete\tDel', self.delete_selected)
        m.exec(ev.screenPos()); ev.accept()

    def _toggle_inline(self, n):
        n.f['inline'] = not n.f.get('inline')
        if n.f['inline']:
            n.f['save'] = ''
            if self.graph.ret_type(n) == 'void':  # the catalog guesses void for many functions that do return something: use the result anyway
                if n.type == 'callgame': n.f['rtype'] = 'auto'
                elif n.type in ('callmethod', 'callext'): n.f['ret'] = 'auto'
        self.commit(keep=[n.id])

    def _add_sel(self, gid):
        ids = self.selected_ids()
        if ids: self.graph.add_to_group(gid, ids); self.commit(keep=ids)

    def _color_group(self, gid, c): self.graph.groups[gid]['color'] = c; self.commit()
    def _color_note(self, nid, c): self.graph.notes[nid]['color'] = c; self.commit()
    def _ungroup(self, gid): self.graph.groups.pop(gid, None); self.commit()
    def _del_note(self, nid): self.graph.notes.pop(nid, None); self.commit()

    def _leave_group(self, nid):
        for v in self.graph.groups.values(): v['nodes'] = [i for i in v['nodes'] if i != nid]
        self.graph._gc(); self.commit(keep=[nid])

    def _select_group(self, gid):
        self.clearSelection()
        for i in self.graph.groups.get(gid, {}).get('nodes', []):
            if i in self.node_items: self.node_items[i].setSelected(True)


class GraphView(QGraphicsView):
    dropped = Signal(str, QPointF)

    def __init__(self, scn):
        super().__init__(scn)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag); self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse); self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate); self.setAcceptDrops(True); self._pan = None; self.centerOn(300, 100)

    def zoom_by(self, f):
        s = self.transform().m11(); ns = min(max(s * f, ZOOM_MIN), ZOOM_MAX)  # clamp instead of refusing: a far-away view can always be zoomed back
        if abs(ns - s) > 1e-9: self.scale(ns / s, ns / s)

    def fit(self):
        r = self.scene().itemsBoundingRect()
        if r.isEmpty(): return
        self.fitInView(r.adjusted(-60, -60, 60, 60), Qt.KeepAspectRatio)
        s = self.transform().m11()
        if s > 1.2: self.setTransform(QTransform.fromScale(1.2, 1.2)); self.centerOn(r.center())
        elif s < ZOOM_MIN: self.setTransform(QTransform.fromScale(ZOOM_MIN, ZOOM_MIN)); self.centerOn(r.center())

    def zoom_percent(self): return round(self.transform().m11() * 100)
    def wheelEvent(self, ev): self.zoom_by(1.12 ** (ev.angleDelta().y() / 120))

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MiddleButton: self._pan = ev.position(); self.setCursor(Qt.ClosedHandCursor); ev.accept(); return
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._pan is not None:
            d = ev.position() - self._pan; self._pan = ev.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(d.x())); self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(d.y())); return
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        if self._pan is not None and ev.button() == Qt.MiddleButton: self._pan = None; self.unsetCursor(); return
        super().mouseReleaseEvent(ev)

    show_grid = True

    def drawBackground(self, p, rect):
        p.fillRect(rect, QColor(C['bg']))
        if self.transform().m11() < 0.5 or not self.show_grid: return
        g = 24; p.setPen(QPen(QColor(C['ln']), 2.2 / self.transform().m11() ** 0.3)); x0, y0 = int(rect.left() // g) * g, int(rect.top() // g) * g
        p.drawPoints(QPolygonF([QPointF(x, y) for x in range(x0, int(rect.right()) + g, g) for y in range(y0, int(rect.bottom()) + g, g)]))

    # drag & drop from the palette: text "odn:<kind>:<value>"
    def dragEnterEvent(self, ev): (ev.acceptProposedAction() if ev.mimeData().text().startswith('odn:') else ev.ignore())
    def dragMoveEvent(self, ev): (ev.acceptProposedAction() if ev.mimeData().text().startswith('odn:') else ev.ignore())
    def dropEvent(self, ev): self.dropped.emit(ev.mimeData().text(), self.mapToScene(ev.position().toPoint())); ev.acceptProposedAction()
