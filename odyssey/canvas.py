"""Work area: nodes, links, zoom/pan, drag & drop (Qt Graphics View)."""
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPainterPathStroker, QPen, QPolygonF, QTransform
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsScene, QGraphicsView, QMenu

from .graph import E
from .theme import C, HEAD_COLORS, pin_color

HEAD, ROW, SUB = 28, 22, 20
F_TITLE, F_PIN, F_SUB = QFont(), QFont(), QFont('Consolas')
F_TITLE.setBold(True); F_TITLE.setPointSizeF(9.5); F_PIN.setPointSizeF(8.5); F_SUB.setPointSizeF(8.5)
FM_T, FM_P = QFontMetricsF(F_TITLE), QFontMetricsF(F_PIN)


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
        self.w = max(190.0, wl + wr + 56, min(FM_T.horizontalAdvance(self.title) + 28, 360.0))
        self.y0 = HEAD + (SUB if self.sub else 0) + 8
        self.h = self.y0 + max(len(self.ins), len(self.outs), 1) * ROW + 6
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True); self.setZValue(1); self.setPos(node.x, node.y); self.setToolTip(self.title)

    def boundingRect(self): return QRectF(-14, -6, self.w + 28, self.h + 12)
    def shape(self):
        p = QPainterPath(); p.addRect(self.boundingRect()); return p

    def pin_pos(self, d, k): return QPointF(0 if d == 'i' else self.w, self.y0 + k * ROW + ROW / 2)
    def pin_index(self, d, pid): return next(i for i, p in enumerate(self.ins if d == 'i' else self.outs) if p.id == pid)

    def pin_at(self, pos):
        best = None
        for d, lst in (('i', self.ins), ('o', self.outs)):
            for k, p in enumerate(lst):
                dist = (self.pin_pos(d, k) - pos).manhattanLength()
                if dist <= 18 and (best is None or dist < best[0]): best = (dist, p.id, d)
        return best[1:] if best else None

    def paint(self, p, opt, widget=None):
        p.setRenderHint(QPainter.Antialiasing); W = self.w
        body = QPainterPath(); body.addRoundedRect(QRectF(0, 0, W, self.h), 10, 10)
        p.fillPath(body, QColor(C['node']))
        p.save(); p.setClipPath(body); p.fillRect(QRectF(0, 0, W, HEAD), QColor(HEAD_COLORS.get(self.node.type, '#6b7385'))); p.restore()
        sel = self.isSelected(); p.setPen(QPen(QColor(C['ac']) if sel else QColor(C['ln']), 2.2 if sel else 1.4)); p.setBrush(Qt.NoBrush); p.drawPath(body)
        p.setFont(F_TITLE); p.setPen(Qt.white)
        p.drawText(QRectF(10, 0, W - 20, HEAD), Qt.AlignVCenter | Qt.AlignLeft, FM_T.elidedText(self.title, Qt.ElideRight, W - 20))
        if self.sub:
            p.setFont(F_SUB); p.setPen(QColor('#b9c0d4')); p.drawText(QRectF(10, HEAD + 1, W - 20, SUB), Qt.AlignVCenter | Qt.AlignLeft, QFontMetricsF(F_SUB).elidedText(self.sub, Qt.ElideRight, W - 20))
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
                    if val: p.setPen(QColor('#7fd6c2')); p.drawText(QRectF(pt.x() + 12 + FM_P.horizontalAdvance(label) + 8, pt.y() - 10, W, 20), Qt.AlignVCenter | Qt.AlignLeft, val)
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
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.node.x, self.node.y = value.x(), value.y(); self.scn.update_edges(); self.scn.moved.emit()
        return super().itemChange(change, value)


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

    def __init__(self, graph):
        super().__init__(); self.graph = graph; self.node_items, self.edge_items = {}, []; self._link = None; self._temp = None; self._lock = False
        self.setSceneRect(-30000, -30000, 60000, 60000); self.selectionChanged.connect(self._sel)

    def _sel(self):
        if self._lock: return
        ids = self.selected_ids(); self.picked.emit(ids[0] if len(ids) == 1 else 0)

    def selected_ids(self): return [i.node.id for i in self.selectedItems() if isinstance(i, NodeItem)]

    def select_only(self, nid):
        self.clearSelection()
        if nid in self.node_items: self.node_items[nid].setSelected(True)

    def rebuild(self, keep=None):
        self._lock = True
        keep = set(self.selected_ids()) if keep is None else set(keep)
        self.graph.prune(); self.clear(); self.node_items, self.edge_items, self._temp = {}, [], None
        for n in self.graph.nodes.values():
            it = NodeItem(self, n); self.addItem(it); self.node_items[n.id] = it; it.setSelected(n.id in keep)
        for e in self.graph.edges:
            it = EdgeItem(self, e); self.addItem(it); self.edge_items.append(it)
        self._lock = False

    def update_edges(self):
        for e in self.edge_items: e.update_path()

    def commit(self, keep=None): self.rebuild(keep); self.changed.emit()

    def remove_edge(self, edge):
        self.graph.edges = [e for e in self.graph.edges if e != edge]; self.commit()

    def delete_selected(self):
        for it in self.selectedItems():
            if isinstance(it, NodeItem): self.graph.remove(it.node.id)
            elif isinstance(it, EdgeItem): self.graph.edges = [e for e in self.graph.edges if e != it.edge]
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
            if hit and self.graph.connect((nid, pid, d), (hit[0].node.id, hit[1][0], hit[1][1])): self.commit()
            ev.accept(); return
        super().mouseReleaseEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        if not [i for i in self.items(ev.scenePos()) if isinstance(i, (NodeItem, EdgeItem))]: self.empty_double.emit(ev.scenePos()); ev.accept(); return
        super().mouseDoubleClickEvent(ev)

    def contextMenuEvent(self, ev):
        it = next((i for i in self.items(ev.scenePos()) if isinstance(i, (NodeItem, EdgeItem))), None)
        if it is None: self.empty_menu.emit(ev.scenePos(), ev.screenPos()); ev.accept(); return
        m = QMenu()
        if isinstance(it, EdgeItem): m.addAction('Delete link', lambda: self.remove_edge(it.edge))
        else:
            if not it.isSelected(): self.clearSelection(); it.setSelected(True)
            m.addAction('Edit…', lambda: self.node_activated.emit(it.node.id)); m.addAction('Duplicate\tCtrl+D', self.duplicate_selected)
            m.addAction('Disconnect all links', lambda: self.unlink(it.node.id)); m.addSeparator(); m.addAction('Delete\tDel', self.delete_selected)
        m.exec(ev.screenPos()); ev.accept()


class GraphView(QGraphicsView):
    dropped = Signal(str, QPointF)

    def __init__(self, scn):
        super().__init__(scn)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag); self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse); self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate); self.setAcceptDrops(True); self._pan = None; self.centerOn(300, 100)

    def zoom_by(self, f):
        s = self.transform().m11()
        if 0.25 <= s * f <= 2.5: self.scale(f, f)

    def fit(self):
        r = self.scene().itemsBoundingRect()
        if r.isEmpty(): return
        self.fitInView(r.adjusted(-60, -60, 60, 60), Qt.KeepAspectRatio)
        if self.transform().m11() > 1.2: self.setTransform(QTransform.fromScale(1.2, 1.2)); self.centerOn(r.center())

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

    def drawBackground(self, p, rect):
        p.fillRect(rect, QColor(C['bg']))
        if self.transform().m11() < 0.5: return
        g = 24; p.setPen(QPen(QColor(C['ln']), 2.2 / self.transform().m11() ** 0.3)); x0, y0 = int(rect.left() // g) * g, int(rect.top() // g) * g
        p.drawPoints(QPolygonF([QPointF(x, y) for x in range(x0, int(rect.right()) + g, g) for y in range(y0, int(rect.bottom()) + g, g)]))

    # drag & drop from the palette: text "odn:<kind>:<value>"
    def dragEnterEvent(self, ev): (ev.acceptProposedAction() if ev.mimeData().text().startswith('odn:') else ev.ignore())
    def dragMoveEvent(self, ev): (ev.acceptProposedAction() if ev.mimeData().text().startswith('odn:') else ev.ignore())
    def dropEvent(self, ev): self.dropped.emit(ev.mimeData().text(), self.mapToScene(ev.position().toPoint())); ev.acceptProposedAction()
