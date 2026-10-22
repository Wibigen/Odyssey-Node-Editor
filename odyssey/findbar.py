"""Search bar floating over the canvas (Ctrl+F): greys out every node that does not use what you typed."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget


class FindBar(QWidget):
    changed = Signal(str)
    step = Signal(int)   # +1 / -1: jump to the next / previous match
    closed = Signal()

    def __init__(self, parent):
        super().__init__(parent); self.setObjectName('findbar'); self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet('#findbar{background:#1d2230;border:1px solid #3a4258;border-radius:10px}')
        h = QHBoxLayout(self); h.setContentsMargins(10, 6, 6, 6); h.setSpacing(6)
        h.addWidget(QLabel('Find'))
        self.edit = QLineEdit(); self.edit.setPlaceholderText('variable, function, expression, value…'); self.edit.setMinimumWidth(260); self.edit.setClearButtonEnabled(True); h.addWidget(self.edit)
        self.count = QLabel('')  ; self.count.setMinimumWidth(70); h.addWidget(self.count)
        self.bPrev, self.bNext, self.bClose = QPushButton('▲'), QPushButton('▼'), QPushButton('✕')
        for b, tip in ((self.bPrev, 'Previous match (Shift+Enter)'), (self.bNext, 'Next match (Enter)'), (self.bClose, 'Close (Esc)')): b.setFixedSize(30, 28); b.setToolTip(tip); b.setStyleSheet('padding:0'); h.addWidget(b)
        self.edit.textChanged.connect(self.changed); self.bNext.clicked.connect(lambda: self.step.emit(1)); self.bPrev.clicked.connect(lambda: self.step.emit(-1)); self.bClose.clicked.connect(self.close_bar)
        self.edit.returnPressed.connect(lambda: self.step.emit(1)); self.hide()

    def open_bar(self, text=None):
        self.show(); self.raise_(); self.place()
        if text is not None and text != '': self.edit.setText(text)
        self.edit.setFocus(); self.edit.selectAll()

    def close_bar(self): self.edit.clear(); self.hide(); self.closed.emit()

    def place(self):
        p = self.parentWidget(); self.adjustSize(); self.move(max(8, p.width() - self.width() - 16), 12)

    def set_count(self, n, cur=0):
        self.count.setText('' if not self.edit.text().strip() else ('no match' if n == 0 else f'{cur}/{n}' if cur else f'{n} found'))
        self.count.setStyleSheet('color:#ff7b7b' if self.edit.text().strip() and n == 0 else 'color:#9aa3b8')

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Escape: self.close_bar(); return
        if ev.key() in (Qt.Key_Return, Qt.Key_Enter) and ev.modifiers() & Qt.ShiftModifier: self.step.emit(-1); return
        super().keyPressEvent(ev)
