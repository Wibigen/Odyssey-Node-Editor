"""Tutorials: the pages (Markdown) of the editor (tutorials/index.json) and the ones enabled plugins ship, in one window next to the editor.

A plugin lists them in plugin.json:  "help": [{"title": "How to use Dear ImGui", "file": "help/using_imgui.md",
                                               "buttons": [{"label": "Load the example", "do": "template:Hello ImGui"}]}]
Button actions ("do"): template:<template name>, base:<plugin id>, browser:<plugin id>, plugins, tour.
The window is not modal: keep it open while you follow the steps in the editor.
"""
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QSplitter, QTextBrowser, QVBoxLayout, QWidget

from .theme import C

CSS = """
body {{ color:{fg}; }} h1 {{ font-size:22px; }} h2 {{ font-size:17px; margin-top:18px; }} a {{ color:{ac}; }}
code {{ background:{bg2}; }} pre {{ background:{bg2}; }} th {{ text-align:left; }} blockquote {{ color:{mu}; }}
"""


def builtin_topics():
    """The editor's own tutorials, from tutorials/index.json: [(section, source, title, path, buttons)]."""
    import json
    from .config import resource
    root = resource('tutorials'); out = []
    try: items = json.loads((root / 'index.json').read_text('utf-8'))
    except Exception: return out
    for it in items:
        f = root / str(it.get('file', ''))
        if f.is_file(): out.append(('Tutorials', 'Odyssey Node Editor', str(it.get('title') or f.stem), f, [(b['label'], b['do']) for b in it.get('buttons', []) if isinstance(b, dict) and b.get('label') and b.get('do')]))
    return out


class HelpDialog(QDialog):
    """topics: [(section, source, page title, path, buttons)]; section is 'Tutorials' (the editor's own) or 'Plugin tutorials'. Emits run(action) for the buttons of a page."""
    run = Signal(str)

    def __init__(self, topics, parent=None, start=0):
        super().__init__(parent); self.setWindowTitle('Tutorials'); self.resize(1000, 720); self.setMinimumSize(640, 420); self.setAttribute(Qt.WA_DeleteOnClose)
        self.topics = topics; v = QVBoxLayout(self)
        top = QHBoxLayout(); self.q = QLineEdit(); self.q.setPlaceholderText('Search in the tutorials…'); self.q.setClearButtonEnabled(True); top.addWidget(self.q, 1); v.addLayout(top)
        sp = QSplitter(); v.addWidget(sp, 1)
        self.lst = QListWidget(); self.lst.setMinimumWidth(190); self.lst.setMaximumWidth(320); sp.addWidget(self.lst)
        right = QWidget(); rv = QVBoxLayout(right); rv.setContentsMargins(8, 0, 0, 0); self.row = QHBoxLayout(); rv.addLayout(self.row)
        self.view = QTextBrowser(); self.view.setOpenLinks(False); self.view.anchorClicked.connect(self.link); self.view.setFont(QFont(self.font().family(), 11))
        self.view.document().setDefaultStyleSheet(CSS.format(fg=C['tx'], ac=C['ac'], bg2=C['bg2'], mu=C['mu'])); rv.addWidget(self.view, 1); sp.addWidget(right); sp.setStretchFactor(1, 3); sp.setSizes([240, 760])
        close = QPushButton('Close'); close.clicked.connect(self.close); b = QHBoxLayout(); b.addStretch(1); b.addWidget(close); v.addLayout(b)
        self.lst.currentRowChanged.connect(self.show_topic); self.q.textChanged.connect(self.fill); self.texts = {}
        self.fill(); self.pick(start)

    def text_of(self, i):
        if i not in self.texts:
            try: self.texts[i] = self.topics[i][3].read_text('utf-8')
            except Exception as e: self.texts[i] = f'# Cannot read this page\n\n{e}'
        return self.texts[i]

    def fill(self, *_):
        words = self.q.text().lower().split(); cur = self.lst.currentItem().data(Qt.UserRole) if self.lst.currentItem() else None; self.lst.blockSignals(True); self.lst.clear(); first = None; last_sec = None
        for i, (sec, src, title, path, btn) in enumerate(self.topics):
            if words and not all(w in (title + ' ' + src + ' ' + self.text_of(i)).lower() for w in words): continue
            if sec != last_sec:  # a heading, not selectable: the editor's tutorials first, then the plugins'
                h = QListWidgetItem(sec.upper()); h.setFlags(Qt.NoItemFlags); f = h.font(); f.setBold(True); f.setPointSizeF(max(8.0, f.pointSizeF() - 1)); h.setFont(f); h.setForeground(QColor(C['mu'])); self.lst.addItem(h); last_sec = sec
            it = QListWidgetItem(title if sec == 'Tutorials' else f'{title}\n{src}'); it.setData(Qt.UserRole, i); self.lst.addItem(it)
            if first is None or i == cur: first = it
        self.lst.blockSignals(False)
        if first is not None: self.lst.setCurrentItem(first); self.show_topic(self.lst.row(first))
        else: self.view.setPlainText('Nothing matches.'); self.clear_buttons()

    def pick(self, i):
        for r in range(self.lst.count()):
            if self.lst.item(r).data(Qt.UserRole) == i: self.lst.setCurrentRow(r); return

    def clear_buttons(self):
        while self.row.count():
            w = self.row.takeAt(0).widget()
            if w: w.hide(); w.setParent(None); w.deleteLater()

    def show_topic(self, row):
        it = self.lst.item(row)
        if it is None or it.data(Qt.UserRole) is None: return
        i = it.data(Qt.UserRole); self.view.setMarkdown(self.text_of(i)); self.view.moveCursor(self.view.textCursor().MoveOperation.Start); self.clear_buttons()
        for label, action in self.topics[i][4]:
            b = QPushButton(label); b.clicked.connect(lambda _=False, a=action: self.run.emit(a)); self.row.addWidget(b)
        self.row.addStretch(1)

    def link(self, url):
        if url.scheme() in ('http', 'https'): QDesktopServices.openUrl(url)
