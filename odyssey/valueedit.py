"""Typed editors for fixed input values (numbers, text, bool, vectors or any C++ expression)."""
import re
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QWidget

from .graph import editor_kind

VEC = re.compile(r'Vector3f?\s*(?:<\s*float\s*>)?\s*[({]\s*([^,]*),\s*([^,]*),\s*([^)}]*)[)}]')
HINTS = {'int': 'integer, 0x… or C++ expression', 'float': 'number (e.g. 1.5) or C++ expression', 'text': 'text (quotes are added for you)'}


def make_editor(t, value, on_change):
    """Return a widget editing a raw value of C++ type `t`; calls on_change(raw) on every edit ('' = unset)."""
    k, value = editor_kind(t), value or ''
    if k == 'bool':
        w = QComboBox()
        for lab, v in (('(not set)', ''), ('true', 'true'), ('false', 'false')): w.addItem(lab, v)
        w.setCurrentIndex(max(0, w.findData(value.lower()))); w.currentIndexChanged.connect(lambda _: on_change(w.currentData())); return w
    if k == 'vec3':
        m = VEC.search(value); vals = [x.strip() for x in m.groups()] if m else ['', '', '']
        w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0); edits = []
        for lab, v in zip('XYZ', vals):
            e = QLineEdit(v); e.setMinimumWidth(30); e.setPlaceholderText(lab); e.setToolTip(f'{lab} component (float)'); edits.append(e); h.addWidget(e)
        def upd():
            xs = [e.text().strip() or '0' for e in edits]; on_change('' if not any(e.text().strip() for e in edits) else f'sead::Vector3f({xs[0]}, {xs[1]}, {xs[2]})')
        for e in edits: e.textEdited.connect(lambda _: upd())
        return w
    e = QLineEdit(value); e.setPlaceholderText(HINTS.get(k, f'C++ expression ({(t or "any type").strip()})')); e.textEdited.connect(on_change); return e
