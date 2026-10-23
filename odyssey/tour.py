"""Interface tour: a short guided presentation of the main window (dimmed screen, the part being explained is highlighted).

Shown the first time the program starts and from Help > Interface tour. It can be skipped at any time (Skip, Esc); once it was completed or skipped it is
not shown at startup again. Closing the program in the middle leaves it unmarked, so it comes back next time.
"""
from PySide6.QtCore import QEvent, QPoint, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QVBoxLayout, QWidget

from .theme import C


def _rect(win, w):
    """Rectangle of a widget in window coordinates, None when it is not visible."""
    if w is None or not w.isVisible() or w.width() < 4 or w.height() < 4: return None
    return QRect(w.mapTo(win, QPoint(0, 0)), w.size())


def _menu_rect(win, title):
    mb = win.menuBar(); menu = mb.findChild(QMenu, 'menu.' + title); m = menu.menuAction() if menu else None
    if m is None or not mb.isVisible(): return None
    r = mb.actionGeometry(m); return QRect(mb.mapTo(win, r.topLeft()), r.size())


def steps(win):
    """[(title, text, rectangle function or None)]. Steps whose target is not visible (a closed dock...) are skipped."""
    mb = lambda: _rect(win, win.menuBar())
    return [
        ('Welcome to the Odyssey Node Editor',
         'This editor turns <b>nodes</b> into the C++ of a <b>Super Mario Odyssey</b> mod (exlaunch). You build the logic on a canvas; the code is written for you.<br><br>'
         'This short tour shows where everything is. Use <b>Next</b> / <b>Back</b> (or the arrow keys); <b>Skip</b> or <b>Esc</b> closes it. You can replay it from <b>Help &gt; Interface tour</b>.', None),
        ('The menus',
         'Everything the editor can do is in the menus: <b>File</b> (new, open, save, templates), <b>Edit</b> (add functions, find, group), <b>Library</b>, <b>View</b>, <b>Tools</b> (compile, settings, shortcuts), <b>Plugins</b> and <b>Help</b>.', mb),
        ('The tool bar',
         'The icons you use most: new / open / save and undo / redo on the left; in the middle clear, fit the view to the graph and search; on the right the red <b>game function browser</b> and the preferences.', lambda: _rect(win, win.gbar)),
        ('Blocks',
         'The list of blocks you can add: flow control, variables, functions, math, pointers and plugin nodes. <b>Double-click</b> or <b>drag</b> a block onto the canvas. Use the buttons at the top to search the thousands of game functions, or the functions added by plugins. '
         'Your saved library functions are at the bottom.', lambda: _rect(win, win.pal)),
        ('The canvas',
         'This is your graph. <b>Drag from a pin</b> to another pin to connect two nodes: the white arrows are the order of execution, the coloured circles are values. Release a link on an empty spot to get a menu that creates and connects a node for you.<br><br>'
         '<b>Mouse wheel</b> zooms, dragging with the <b>middle button</b> moves the view, <b>right-click</b> on the empty canvas adds things, <b>F</b> fits everything.', lambda: _rect(win, win.view)),
        ('The inspector',
         'Select a node to see and edit it here: its signature, fixed values for the inputs that are not wired, its settings (for example <i>Hook</i> before / after), and buttons to duplicate, disconnect or delete it.', lambda: _rect(win, win.insp)),
        ('The generated code',
         'The <b>C++ code</b> tab shows the code the graph produces, live; the lines of the selected node are highlighted. <b>Includes</b> lists the headers, <b>Problems</b> tells you what is missing or wrong before you compile, <b>Build</b> shows the compiler output and <b>Ryujinx</b> installs and launches your mod.', lambda: _rect(win, win.tabs)),
        ('Write, compile, test',
         '<b>Write to project</b> (Ctrl+E) saves the code into your exlaunch project, <b>Compile</b> (F5) builds it. Set your project and build command once in <b>Tools &gt; Settings</b>. Then use the <b>Ryujinx</b> tab to try the mod.',
         lambda: (lambda a, b: a.united(b) if a and b else a or b)(_rect(win, win.bWrite), _rect(win, win.bBuild))),
        ('Plugins',
         'Plugins add nodes, whole function catalogs, themes and templates. <b>Dear ImGui</b> (in-game windows) is bundled but off by default: switch it on in the <b>Plugin explorer</b>. Nodes that come from a plugin have a soft coloured glow on the canvas.', lambda: _menu_rect(win, 'Plugins')),
        ('Tutorials',
         'The <b>Tutorials</b> window has step-by-step guides on every part of the editor, then the guides shipped by your plugins. Press <b>F1</b> to open it any time and keep it next to the editor while you work.', lambda: _menu_rect(win, 'Help')),
        ('You are ready',
         'A good first project: open <b>Tutorials &gt; Your first mod</b>, or load an example from <b>File &gt; New from template</b>. Have fun!', None),
    ]


class Tour(QWidget):
    finished = Signal(bool)   # True = completed, False = skipped

    def __init__(self, win):
        super().__init__(win); self.win, self.i, self.open_tut, self._done = win, -1, False, False
        self.setFocusPolicy(Qt.StrongFocus); self.setMouseTracking(True); self.hole = QRect()
        self.steps = steps(win); self.card = QFrame(self); self.card.setObjectName('tourcard')
        self.card.setStyleSheet(f"#tourcard{{background:{C['pn']};border:1px solid {C['ac']};border-radius:12px}} QLabel{{background:transparent}}")
        v = QVBoxLayout(self.card); v.setContentsMargins(18, 14, 18, 14); v.setSpacing(8)
        self.count = QLabel(); self.count.setStyleSheet(f"color:{C['mu']};font-size:11px"); self.title = QLabel(); self.title.setStyleSheet('font-size:17px;font-weight:600'); self.title.setWordWrap(True)
        self.text = QLabel(); self.text.setWordWrap(True); self.text.setTextFormat(Qt.RichText); self.text.setStyleSheet(f"color:{C['tx']}")
        for w in (self.count, self.title, self.text): v.addWidget(w)
        row = QHBoxLayout(); self.bSkip, self.bBack, self.bTut, self.bNext = QPushButton('Skip tour'), QPushButton('Back'), QPushButton('Open the tutorials'), QPushButton('Next')
        self.bSkip.setFlat(True); self.bNext.setObjectName('pri'); self.bNext.setDefault(True)
        for b in (self.bSkip,): row.addWidget(b)
        row.addStretch(1)
        for b in (self.bBack, self.bTut, self.bNext): row.addWidget(b)
        v.addLayout(row); self.card.setFixedWidth(400)
        self.bSkip.clicked.connect(lambda: self.finish(False)); self.bBack.clicked.connect(lambda: self.go(-1)); self.bNext.clicked.connect(lambda: self.go(1)); self.bTut.clicked.connect(self.tutorials)
        win.installEventFilter(self); self.hide()

    # ---- flow ----
    def start(self):
        self.setGeometry(self.win.rect()); self.raise_(); self.show(); self.setFocus(); self.go(1)

    def go(self, d):
        j = self.i + d
        while 0 <= j < len(self.steps) and self.target(j) is False: j += d   # skip a step whose part of the window is hidden
        if j >= len(self.steps): self.finish(True); return
        if j < 0: return
        self.i = j; self.show_step()

    def target(self, j):
        """QRect of the step, None for a centred step, False when its target is not visible."""
        fn = self.steps[j][2]
        if fn is None: return None
        r = fn(); return r if r is not None else False

    def show_step(self):
        title, text, _ = self.steps[self.i]; last = self.i == len(self.steps) - 1
        self.count.setText(f'{self.i + 1} / {len(self.steps)}'); self.title.setText(title); self.text.setText(text)
        self.bBack.setEnabled(self.i > 0); self.bNext.setText('Finish' if last else 'Next'); self.bTut.setVisible(last); self.bSkip.setVisible(not last)
        self.layout_card(); self.update(); self.setFocus()

    def layout_card(self):
        self.card.adjustSize(); cw, ch = self.card.width(), self.card.sizeHint().height(); self.card.resize(cw, ch); W, H = self.width(), self.height()
        r = self.target(self.i); r = r if isinstance(r, QRect) else None
        if r is None: self.hole = QRect(); self.card.move((W - cw) // 2, (H - ch) // 2); return
        self.hole = r.adjusted(-6, -6, 6, 6).intersected(self.rect()); g, h = 18, self.hole
        for x, y in ((h.right() + g, h.top()), (h.left() - g - cw, h.top()), (h.left(), h.bottom() + g), (h.left(), h.top() - g - ch)):
            if 8 <= x and x + cw <= W - 8 and 8 <= y and y + ch <= H - 8: self.card.move(x, y); return
            x2, y2 = min(max(8, x), W - cw - 8), min(max(8, y), H - ch - 8)
            if not QRect(x2, y2, cw, ch).intersects(h): self.card.move(x2, y2); return
        self.card.move(min(max(8, h.center().x() - cw // 2), W - cw - 8), min(max(8, h.bottom() - ch - 24), H - ch - 8))  # no free side: inside the highlighted area

    def tutorials(self):
        self.open_tut = True; self.finish(True)

    def finish(self, completed):
        if self._done: return
        self._done = True; self.win.removeEventFilter(self); self.hide(); self.finished.emit(completed); self.deleteLater()

    # ---- events ----
    def eventFilter(self, o, ev):
        if o is self.win and ev.type() in (QEvent.Resize, QEvent.Move) and self.isVisible(): self.setGeometry(self.win.rect()); self.layout_card(); self.update()
        return False

    def keyPressEvent(self, ev):
        k = ev.key()
        if k == Qt.Key_Escape: self.finish(False)
        elif k in (Qt.Key_Right, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space): self.go(1)
        elif k == Qt.Key_Left: self.go(-1)
        else: ev.ignore()

    def mousePressEvent(self, ev): ev.accept()   # the editor is not clickable behind the tour
    def wheelEvent(self, ev): ev.accept()

    def paintEvent(self, ev):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); path = QPainterPath(); path.addRect(QRectF(self.rect()))
        if not self.hole.isNull():
            hole = QPainterPath(); hole.addRoundedRect(QRectF(self.hole), 10, 10); path = path.subtracted(hole)
        p.fillPath(path, QColor(0, 0, 0, 165))
        if not self.hole.isNull(): p.setBrush(Qt.NoBrush); p.setPen(QPen(QColor(C['ac']), 2.4)); p.drawRoundedRect(QRectF(self.hole), 10, 10)
