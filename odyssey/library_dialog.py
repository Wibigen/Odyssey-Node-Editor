"""Manage the saved functions (.odnf files in your data folder): insert, rename, delete."""
import json
from pathlib import Path
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout)

from . import library
from .config import LIBDIR


class LibraryDialog(QDialog):
    insert_requested = Signal(str)  # path of the .odnf file

    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle('Function library'); self.resize(560, 460); v = QVBoxLayout(self)
        v.addWidget(QLabel('Functions and templates you saved. Inserting one adds copies of its nodes inside a group, so you can keep reusing them.'))
        self.list = QListWidget(); v.addWidget(self.list, 1); self.info = QLabel(); self.info.setStyleSheet('color:#8a91a5'); self.info.setWordWrap(True); v.addWidget(self.info)
        row = QHBoxLayout(); self.bIns, self.bRen, self.bDel, self.bDir, self.bClose = (QPushButton(t) for t in ('Insert into graph', 'Rename / describe…', 'Delete', 'Open folder', 'Close'))
        self.bIns.setObjectName('pri')
        for b in (self.bIns, self.bRen, self.bDel, self.bDir): row.addWidget(b)
        row.addStretch(1); row.addWidget(self.bClose); v.addLayout(row)
        self.bIns.clicked.connect(self.insert); self.bRen.clicked.connect(self.rename); self.bDel.clicked.connect(self.delete); self.bClose.clicked.connect(self.accept)
        self.bDir.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(LIBDIR)))); self.list.itemDoubleClicked.connect(lambda _: self.insert())
        self.list.currentItemChanged.connect(self.show_info); self.fill()

    def fill(self):
        self.list.clear()
        for p, name, desc, n in library.entries():
            it = QListWidgetItem(f'{name}   ({n} nodes)'); it.setData(Qt.UserRole, str(p)); it.setData(Qt.UserRole + 1, (name, desc)); self.list.addItem(it)
        if self.list.count(): self.list.setCurrentRow(0)
        self.show_info(self.list.currentItem())

    def cur(self): it = self.list.currentItem(); return (it.data(Qt.UserRole), *it.data(Qt.UserRole + 1)) if it else None

    def show_info(self, it):
        c = self.cur(); self.info.setText((c[2] or 'No description.') + f'\n{c[0]}' if c else 'The library is empty. Select a function or some nodes and use Library > Save selection to library.')
        for b in (self.bIns, self.bRen, self.bDel): b.setEnabled(bool(c))

    def insert(self):
        c = self.cur()
        if c: self.insert_requested.emit(c[0])

    def rename(self):
        c = self.cur()
        if not c: return
        name, ok = QInputDialog.getText(self, 'Library', 'Name:', text=c[1])
        if not ok or not name.strip(): return
        desc, ok = QInputDialog.getMultiLineText(self, 'Library', 'Description (optional):', c[2])
        if not ok: return
        j = library.load(c[0]); j['name'], j['desc'] = name.strip(), desc
        p = Path(c[0]); new = LIBDIR / (library.safe_name(name) + library.EXT); new.write_text(json.dumps(j, indent=1), 'utf-8')
        if new != p: p.unlink(missing_ok=True)
        self.fill()

    def delete(self):
        c = self.cur()
        if c and QMessageBox.question(self, 'Library', f'Delete "{c[1]}" from your library?') == QMessageBox.Yes:
            Path(c[0]).unlink(missing_ok=True); self.fill()
