"""Interface languages.

The program is written in English; another language is a catalog {English text: translation} in lang/<code>.json (a copy in your data folder, lang/ next to
your settings, can add a language or override a text). Texts with variables use {0} {1}... and are looked up before they are filled in: tr('Opened: {0}', path).

* tr(text, *args)    translate (and fill in). Alias: _
* Qt widgets          once a language other than English is chosen, install_qt() wraps the Qt calls that show text (setText, setToolTip, addAction, QMessageBox...)
                      so the texts that go through them are translated without touching every call site.
* The language is chosen in View > Language (globe icon) and applied at the next start.
"""
import json, re, os
from pathlib import Path

from .config import DATA, resource

LANGS = [('en', 'English'), ('fr', 'Français'), ('de', 'Deutsch'), ('es', 'Español'), ('it', 'Italiano'), ('nl', 'Nederlands'), ('ru', 'Русский'), ('ja', '日本語'), ('zh', '中文（简体）')]
QT_CODE = {'zh': 'zh_CN'}   # name of the Qt translation file (standard buttons, file dialogs)
CUR, CAT, MISSING = 'en', {}, set()
DEBUG = bool(os.environ.get('ODN_I18N_DEBUG'))
KEYS = re.compile(r'^(Ctrl|Shift|Alt|Meta|F\d+|Del|Space|Tab|Esc|Enter|Return|Backspace|Home|End|Up|Down|Left|Right|PgUp|PgDown|Ins)([+, ].*)?$|^[A-Z0-9]$')


def codes(): return [c for c, _ in LANGS]


def pack_dirs(): return [resource('lang'), DATA / 'lang']


def load_catalog(code):
    cat = {}
    if code == 'en': return cat
    for d in pack_dirs():
        f = Path(d) / f'{code}.json'
        try: cat.update({k: v for k, v in json.loads(f.read_text('utf-8')).items() if isinstance(v, str) and v})
        except Exception: pass
    return cat


def set_language(code):
    global CUR, CAT
    CUR = code if code in codes() else 'en'; CAT = load_catalog(CUR); return CUR


def lookup(s, cat=None):
    """Translation of one text, or the text itself. Tolerates the extra bits code adds around a text: spaces, a shortcut hint '  (Ctrl+S)', a trailing colon."""
    cat = CAT if cat is None else cat
    if not cat or not isinstance(s, str) or not s.strip(): return s
    r = cat.get(s)
    if r is not None: return r
    lead, core = s[:len(s) - len(s.lstrip())], s.strip()
    tail = s[len(s.rstrip()):]
    if (lead or tail) and core in cat: return lead + cat[core] + tail
    m = re.match(r'^(.*?)(\s+\(([^()]*)\))$', core)   # 'Game function…  (Ctrl+Shift+F)'
    if m and KEYS.match(m[3]) and m[1] in cat: return lead + cat[m[1]] + m[2] + tail
    if DEBUG and re.search('[A-Za-z]{3}', core): MISSING.add(s)
    return s


def tr(text, *args):
    out = lookup(text)
    if args:
        try: return out.format(*args)
        except Exception:
            try: return text.format(*args)
            except Exception: return out
    return out


_ = tr


def tr_n(one, many, n):
    """Plural: tr_n('{0} node', '{0} nodes', n). (Languages here need only one / many; the catalog can word each form.)"""
    return tr(one if n == 1 else many, n)


def localized(path):
    """A page in the current language: <folder>/<code>/<name> when it exists (tutorials/fr/01_start.md), else the page itself (English)."""
    p = Path(path)
    if CUR != 'en':
        q = p.parent / CUR / p.name
        if q.is_file(): return q
    return p


def tr_in(code, text, *args):
    """Translate into a given language (used to ask 'restart now?' in the language just chosen)."""
    out = lookup(text, load_catalog(code))
    try: return out.format(*args) if args else out
    except Exception: return out


# ---------------- Qt ----------------
_done = False


def _t(v):
    return lookup(v) if isinstance(v, str) and len(v) < 4000 else v


def install_qt(app):
    """Wrap the Qt calls that show text, and load Qt's own translation (OK / Cancel / Save…, file dialogs). Does nothing for English."""
    global _done
    if CUR == 'en' or _done: return
    _done = True
    from PySide6.QtCore import QCoreApplication, QLibraryInfo, QTranslator
    from PySide6.QtGui import QAction, QIcon
    from PySide6 import QtWidgets as W
    tl = QTranslator(app)
    if tl.load(f'qtbase_{QT_CODE.get(CUR, CUR)}', QLibraryInfo.path(QLibraryInfo.TranslationsPath)): app.installTranslator(tl); app._odn_tl = tl

    def wrap(cls, name, make):
        orig = getattr(cls, name, None)
        if orig is None: return
        try: setattr(cls, name, make(orig))
        except Exception: pass

    def first_str(idx=0):   # translate the str args (all of them) at the given positions
        def make(orig):
            def f(self, *a, **k):
                a = [_t(x) if (i in range(idx, idx + 1) or idx < 0) else x for i, x in enumerate(a)] if idx >= 0 else [_t(x) for x in a]
                return orig(self, *a, **k)
            return f
        return make

    def all_str(orig):
        def f(self, *a, **k): return orig(self, *[_t(x) for x in a], **k)
        return f

    def after_icon(orig):    # (text, ...) or (icon, text, ...)
        def f(self, *a, **k):
            a = list(a)
            if a:
                i = 1 if isinstance(a[0], QIcon) else 0
                if len(a) > i: a[i] = _t(a[i])
            return orig(self, *a, **k)
        return f

    def listarg(orig):
        def f(self, *a, **k): return orig(self, *[[_t(y) for y in x] if isinstance(x, (list, tuple)) else _t(x) for x in a], **k)
        return f

    def static_args(*idx):
        def make(orig):
            def f(*a, **k): return orig(*[_t(x) if i in idx else x for i, x in enumerate(a)], **k)
            return f
        return make

    def short_text(orig):    # setPlainText / appendPlainText: a short message is translated, a whole source file never
        def f(self, s, *a, **k): return orig(self, _t(s) if isinstance(s, str) and len(s) < 300 and '\n' not in s.strip() else s, *a, **k)
        return f

    def ctor(idxs):
        def make(orig):
            def f(self, *a, **k):
                a = [_t(x) if i in idxs and isinstance(x, str) else ([_t(y) for y in x] if i in idxs and isinstance(x, (list, tuple)) else x) for i, x in enumerate(a)]
                return orig(self, *a, **k)
            return f
        return make

    for c in (W.QLabel, W.QAbstractButton, W.QGroupBox):
        wrap(c, 'setText' if c is not W.QGroupBox else 'setTitle', all_str)
    wrap(W.QGroupBox, 'setTitle', all_str); wrap(W.QMenu, 'setTitle', all_str); wrap(QAction, 'setText', all_str); wrap(QAction, 'setToolTip', all_str); wrap(QAction, 'setStatusTip', all_str)
    for n in ('setToolTip', 'setStatusTip', 'setWindowTitle'): wrap(W.QWidget, n, all_str)
    wrap(W.QLineEdit, 'setPlaceholderText', all_str); wrap(W.QPlainTextEdit, 'setPlaceholderText', all_str)
    wrap(W.QStatusBar, 'showMessage', first_str(0)); wrap(W.QSpinBox, 'setSuffix', all_str); wrap(W.QSpinBox, 'setPrefix', all_str)
    for n in ('setPlainText', 'appendPlainText'): wrap(W.QPlainTextEdit, n, short_text)
    wrap(W.QTabWidget, 'addTab', all_str); wrap(W.QTabWidget, 'setTabText', all_str); wrap(W.QTabBar, 'setTabText', all_str); wrap(W.QComboBox, 'setItemText', all_str)
    wrap(W.QComboBox, 'addItem', after_icon); wrap(W.QMenu, 'addMenu', after_icon); wrap(W.QMenu, 'addAction', after_icon); wrap(W.QMenuBar, 'addMenu', after_icon); wrap(W.QMenuBar, 'addAction', after_icon)
    wrap(W.QFormLayout, 'addRow', first_str(0)); wrap(W.QTableWidget, 'setHorizontalHeaderLabels', listarg); wrap(W.QTreeWidget, 'setHeaderLabels', listarg)
    wrap(W.QTreeWidgetItem, 'setText', lambda orig: (lambda self, col, s: orig(self, col, _t(s)))); wrap(W.QListWidgetItem, 'setText', all_str); wrap(W.QTableWidgetItem, 'setText', all_str)
    for n in ('setText', 'setInformativeText', 'setDetailedText', 'setWindowTitle'): wrap(W.QMessageBox, n, all_str)
    wrap(W.QMessageBox, 'setButtonText', lambda orig: (lambda self, b, s: orig(self, b, _t(s))))
    for n in ('information', 'warning', 'critical', 'question', 'about'): wrap(W.QMessageBox, n, static_args(1, 2))
    wrap(W.QFileDialog, 'getOpenFileName', static_args(1, 3)); wrap(W.QFileDialog, 'getSaveFileName', static_args(1, 3)); wrap(W.QFileDialog, 'getExistingDirectory', static_args(1))
    wrap(W.QInputDialog, 'getText', static_args(1, 2)); wrap(W.QInputDialog, 'getItem', static_args(1, 2))
    for c, idx in ((W.QLabel, (0,)), (W.QPushButton, (0, 1)), (W.QCheckBox, (0,)), (W.QRadioButton, (0,)), (W.QGroupBox, (0,)), (QAction, (0, 1)), (W.QMenu, (0,)), (W.QDockWidget, (0,)),
                   (W.QListWidgetItem, (0, 1)), (W.QTableWidgetItem, (0, 1)), (W.QTreeWidgetItem, (0,)), (W.QToolButton, ()), (W.QMessageBox, (1, 2))):
        if idx: wrap(c, '__init__', ctor(set(idx)))
