"""Change the return type of a game function (the catalog guesses it from headers and is sometimes wrong)."""
from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QLabel, QMessageBox, QVBoxLayout

from .config import load_config, save_config
from .graph import COMMON_TYPES


class RetTypeDialog(QDialog):
    def __init__(self, parent, name, current, guess, remembered):
        super().__init__(parent); self.setWindowTitle('Return type'); self.setMinimumWidth(460); v = QVBoxLayout(self)
        lab = QLabel(f'<b>{name}</b><br>The catalog says it returns <b>{guess}</b>.'); lab.setWordWrap(True); v.addWidget(lab)
        self.t = QComboBox(); self.t.setEditable(True); self.t.addItems([x for x in dict.fromkeys([current, guess, 'void', *COMMON_TYPES]) if x]); self.t.setEditText(current); v.addWidget(self.t)
        self.remember = QCheckBox('Use this type for every call of this function (remembered in your settings)'); self.remember.setChecked(remembered); v.addWidget(self.remember)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); v.addWidget(bb)


def ask_ret_type(parent, graph, sym, current):
    """Warn, then let the user type another return type. Returns (type, remember) or None if cancelled."""
    c = graph.cat.get(sym) or {}
    ok = QMessageBox.warning(parent, 'Change the return type?',
                             'The catalog guesses return types by reading header files, so it can be wrong (a function shown as void may really return something).\n\n'
                             'A wrong type makes the generated call read garbage or crash the game. Only change it if you checked the real signature, for example in the decompiled source.',
                             QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
    if ok != QMessageBox.Yes: return None
    d = RetTypeDialog(parent, c.get('n', sym), current, c.get('r', ''), sym in graph.overrides)
    if not d.exec(): return None
    t = d.t.currentText().strip()
    return (t, d.remember.isChecked()) if t else None


def remember(graph, sym, t):
    """Keep (or forget, if t is empty) a return type for every call of a game function."""
    if t: graph.overrides[sym] = t
    else: graph.overrides.pop(sym, None)
    cfg = load_config(); cfg['ret_overrides'] = dict(graph.overrides); save_config(cfg)
