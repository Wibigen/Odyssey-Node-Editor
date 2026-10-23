"""Keyboard shortcuts: one row per command, click a shortcut and press the new keys."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QKeySequenceEdit, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QHeaderView)

from .icons import bind
from .theme import C


def pretty(seq):
    return QKeySequence(seq).toString(QKeySequence.NativeText) if seq else ''


class ShortcutsDialog(QDialog):
    """entries: [(id, label, default 'Ctrl+N', current 'Ctrl+N')]  ->  result(): {id: 'Ctrl+X'} for every command that differs from its default ('' = no shortcut)."""

    def __init__(self, entries, parent=None):
        super().__init__(parent); self.setWindowTitle('Keyboard shortcuts'); self.resize(640, 560)
        self.rows = [dict(id=i, label=l, default=d or '', cur=c or '') for i, l, d, c in entries]; v = QVBoxLayout(self)
        hint = QLabel('Click a shortcut, then press the keys you want. Backspace / Delete clears it. A command can have one shortcut.'); hint.setWordWrap(True); hint.setStyleSheet(f"color:{C['mu']}"); v.addWidget(hint)
        self.q = QLineEdit(); self.q.setPlaceholderText('Search a command…'); self.q.setClearButtonEnabled(True); self.q.textChanged.connect(self.filter); v.addWidget(self.q)
        self.t = QTableWidget(len(self.rows), 3); self.t.setHorizontalHeaderLabels(['Command', 'Shortcut', 'Default']); self.t.verticalHeader().setVisible(False); self.t.setSelectionBehavior(QTableWidget.SelectRows)
        self.t.setEditTriggers(QTableWidget.NoEditTriggers); self.t.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch); self.t.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents); v.addWidget(self.t, 1)
        self.edit = QKeySequenceEdit(); self.edit.setMaximumSequenceLength(1); self.edit.setVisible(False); self.edit.editingFinished.connect(self.commit); self.edit_row = -1
        self.msg = QLabel(); self.msg.setWordWrap(True); v.addWidget(self.msg)
        row = QHBoxLayout(); self.bReset, self.bAll = QPushButton('Reset this one'), QPushButton('Reset all'); self.bClear = QPushButton('Clear')
        for b in (self.bReset, self.bClear, self.bAll): row.addWidget(b)
        row.addStretch(1); bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(self.try_accept); bb.rejected.connect(self.reject); row.addWidget(bb); v.addLayout(row)
        self.t.cellClicked.connect(self.begin); self.t.currentCellChanged.connect(lambda r, *_: self.hide_edit())
        self.bReset.clicked.connect(self.reset_one); self.bClear.clicked.connect(self.clear_one); self.bAll.clicked.connect(self.reset_all); self.paint()

    # ---- table ----
    def paint(self):
        self.t.blockSignals(True)
        dup = self.conflicts()
        for r, d in enumerate(self.rows):
            for c, txt in enumerate((d['label'], pretty(d['cur']) or '—', pretty(d['default']) or '—')):
                it = self.t.item(r, c) or QTableWidgetItem(); it.setText(txt); self.t.setItem(r, c, it)
                it.setForeground(Qt.red if (c == 1 and d['cur'] and d['cur'] in dup) else self.t.palette().text())
                f = it.font(); f.setBold(c == 1 and d['cur'] != d['default']); it.setFont(f)
        self.t.blockSignals(False)
        names = {k: [d['label'] for d in self.rows if d['cur'] == k] for k in dup}
        self.msg.setText('<span style="color:#d63c3c">Used twice: ' + '; '.join(f"{pretty(k)} ({', '.join(v)})" for k, v in names.items()) + '</span>' if names else '')

    def conflicts(self):
        seen, dup = {}, set()
        for d in self.rows:
            if d['cur']:
                if d['cur'] in seen: dup.add(d['cur'])
                seen[d['cur']] = 1
        return dup

    def filter(self, text):
        q = text.lower().strip()
        for r, d in enumerate(self.rows): self.t.setRowHidden(r, bool(q) and q not in d['label'].lower() and q not in pretty(d['cur']).lower())

    # ---- recording ----
    def begin(self, r, c):
        self.hide_edit(); self.edit_row = r; rect = self.t.visualRect(self.t.model().index(r, 1)); self.edit.setParent(self.t.viewport()); self.edit.setGeometry(rect); self.edit.clear(); self.edit.setVisible(True); self.edit.setFocus()

    def hide_edit(self):
        if self.edit.isVisible(): self.edit.setVisible(False)

    def commit(self):
        ks = self.edit.keySequence()
        if self.edit_row >= 0 and not ks.isEmpty():
            self.rows[self.edit_row]['cur'] = ks.toString(QKeySequence.PortableText)
            self.edit.setVisible(False); self.paint()

    def selected(self):
        r = self.t.currentRow(); return self.rows[r] if 0 <= r < len(self.rows) else None

    def reset_one(self):
        d = self.selected()
        if d: d['cur'] = d['default']; self.paint()

    def clear_one(self):
        d = self.selected()
        if d: d['cur'] = ''; self.paint()

    def reset_all(self):
        for d in self.rows: d['cur'] = d['default']
        self.paint()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Backspace, Qt.Key_Delete) and self.edit.isVisible(): self.clear_one(); self.hide_edit(); return
        super().keyPressEvent(e)

    def try_accept(self):
        if self.conflicts(): QMessageBox.warning(self, 'Keyboard shortcuts', 'Some commands use the same shortcut (shown in red). Change one of them first.'); return
        self.accept()

    def result(self):
        return {d['id']: d['cur'] for d in self.rows if d['cur'] != d['default']}
