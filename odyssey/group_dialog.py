"""Create / edit a group: name, color (named) and which nodes belong to it."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout

from .graph import COLOR_NAMES


def swatch(hex_):
    pm = QPixmap(16, 16); pm.fill(QColor(hex_)); return QIcon(pm)


class GroupDialog(QDialog):
    def __init__(self, graph, gid=None, preselected=(), parent=None):
        """gid=None creates a group from `preselected` node ids."""
        super().__init__(parent); self.graph, self.gid = graph, gid; self.setWindowTitle('New group' if gid is None else 'Edit group'); self.setMinimumSize(440, 520); v = QVBoxLayout(self)
        gr = graph.groups.get(gid, {}) if gid is not None else {}
        f = QFormLayout(); v.addLayout(f); self.name = QLineEdit(gr.get('name', 'Group')); f.addRow('Name', self.name)
        self.color = QComboBox()
        for nm, c in COLOR_NAMES.items(): self.color.addItem(swatch(c), nm, c)
        cur = gr.get('color') or list(COLOR_NAMES.values())[(graph.gid - 1) % len(COLOR_NAMES)]
        if cur not in COLOR_NAMES.values(): self.color.addItem(swatch(cur), 'Custom', cur)
        self.color.setCurrentIndex(max(0, self.color.findData(cur))); f.addRow('Color', self.color)
        v.addWidget(QLabel('Nodes in this group (tick to add, untick to remove). A node can only be in one group.'))
        self.lst = QListWidget(); v.addWidget(self.lst, 1)
        mine = set(gr.get('nodes', [])) | set(preselected)
        for n in sorted(graph.nodes.values(), key=lambda n: (graph.group_of(n.id) not in (gid, None), n.id)):
            other = graph.group_of(n.id); title = graph.spec(n)[0]
            it = QListWidgetItem(f'#{n.id}  {title}' + (f'    (now in "{graph.groups[other]["name"]}")' if other not in (None, gid) else '')); it.setData(Qt.UserRole, n.id)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable); it.setCheckState(Qt.Checked if n.id in mine else Qt.Unchecked); self.lst.addItem(it)
        row = QHBoxLayout(); v.addLayout(row)
        for t, fn in (('Select all', lambda: self.setall(Qt.Checked)), ('Select none', lambda: self.setall(Qt.Unchecked))):
            b = QPushButton(t); b.clicked.connect(fn); row.addWidget(b)
        row.addStretch(1)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); v.addWidget(bb)

    def setall(self, st):
        for i in range(self.lst.count()): self.lst.item(i).setCheckState(st)

    def apply(self):
        ids = [self.lst.item(i).data(Qt.UserRole) for i in range(self.lst.count()) if self.lst.item(i).checkState() == Qt.Checked]
        name, col = self.name.text().strip() or 'Group', self.color.currentData()
        if self.gid is None: return self.graph.make_group(ids, name, col)
        gr = self.graph.groups[self.gid]; gr['name'], gr['color'] = name, col
        for k, v in self.graph.groups.items(): v['nodes'] = [i for i in v['nodes'] if k == self.gid or i not in ids]
        gr['nodes'] = ids; self.graph._gc(); return self.gid
