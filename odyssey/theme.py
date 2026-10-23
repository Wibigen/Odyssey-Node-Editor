"""Dark theme (Qt palette + stylesheet) and node / pin colors."""
import re
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from .config import resource

PALETTES = {
    'dark': dict(bg='#14161c', bg2='#1a1d25', pn='#20242e', node='#232834', ln='#2f3441', grid='#242834', tx='#e9ebf1', mu='#8a91a5', ok='#4ecb8a', ko='#ef5b5b', val='#7fd6c2', warn='#ffd166', sub='#b9c0d4', bar='#1d2230',
                 code_num='#6dd26d', code_kw='#6aa7ff', code_pp='#c792ea', code_str='#e6b673', code_cm='#7f8aa3'),
    'light': dict(bg='#f2f3f7', bg2='#ffffff', pn='#e7e9f0', node='#ffffff', ln='#c9cdd9', grid='#d6d9e3', tx='#1b2030', mu='#5f677c', ok='#1f9d62', ko='#d63c3c', val='#0d8a76', warn='#8a5d00', sub='#586078', bar='#ffffff',
                  code_num='#1d8a3a', code_kw='#1f5fd0', code_pp='#8a3fc4', code_str='#b25e00', code_cm='#7b8499'),
}
ACCENTS = {'Red': '#e8484f', 'Orange': '#e8863a', 'Amber': '#d99a00', 'Green': '#2fa66a', 'Teal': '#14a3a3', 'Blue': '#3a7bd5', 'Purple': '#9a66e8', 'Pink': '#e0559c'}
C = dict(PALETTES['dark'], ac=ACCENTS['Red'], mode='dark')
PLUGIN_THEMES = {}  # 'plugin.theme' -> dict(name, base, colors, accent, plugin): themes added by plugins


def register_theme(key, name, base='dark', colors=None, accent='', plugin=''):
    """Add a theme. colors only needs the entries to change (keys of PALETTES['dark']); the rest comes from the base palette."""
    PLUGIN_THEMES[key] = dict(name=name, base=base if base in PALETTES else 'dark', colors={k: v for k, v in (colors or {}).items() if k in PALETTES['dark'] and re.fullmatch(r'#[0-9a-fA-F]{6}', str(v))},
                              accent=accent if re.fullmatch(r'#[0-9a-fA-F]{6}', str(accent or '')) else '', plugin=plugin)


def theme_choices():
    """[(key, label, base)] : the two built-in themes, then the ones from plugins."""
    return [('dark', 'Dark', 'dark'), ('light', 'Light', 'light')] + [(k, t['name'], t['base']) for k, t in PLUGIN_THEMES.items()]


def set_theme(mode='dark', accent='Red'):
    """Switch the shared color table in place (every module reads C when it paints). Call apply_theme afterwards for the Qt widgets."""
    t = PLUGIN_THEMES.get(mode); base = t['base'] if t else (mode if mode in PALETTES else 'dark')
    C.update(PALETTES[base]); C['mode'] = base
    if t: C.update(t['colors'])
    C['ac'] = ACCENTS.get(accent) or (accent if str(accent).startswith('#') else '') or (t['accent'] if t else '') or ACCENTS['Red']
    if accent == 'Theme': C['ac'] = (t['accent'] if t and t['accent'] else ACCENTS['Red'])
GREEN, ORANGE, TEAL, BLUE, PURPLE = '#4f9a4f', '#c46a2d', '#14a3a3', '#3a7bd5', '#9a66e8'
HEAD_COLORS = dict(hook='#e8484f', callorig='#e8484f', callmethod='#2fa66a', callext='#2fa66a', func=PURPLE, callfn=PURPLE, callgame='#2fa66a', if_=BLUE, switch=BLUE, **{'for': BLUE, 'while': BLUE, 'ret': BLUE, 'if': BLUE},
                   local=TEAL, setvar=TEAL, getvar=TEAL, literal='#7a7f90', op=GREEN, cmp=GREEN, logic=GREEN, **{'not': GREEN, 'global': TEAL},
                   addr=ORANGE, deref=ORANGE, isnull=ORANGE, cast=ORANGE, member=ORANGE, setmember=ORANGE, readoff=ORANGE, writeoff=ORANGE, stmt='#c98a2b', expr='#c98a2b')


def pin_color(t):
    """Pin color for a C++ type."""
    if re.search(r'\*', t or ''): return '#f0a04b'
    if t == 'bool': return '#ef5b5b'
    if re.fullmatch(r'(unsigned )?(int|long|short|char|[us](8|16|32|64))', t or ''): return '#35c4d6'
    if re.fullmatch(r'float|f32|double|f64', t or ''): return '#6dd26d'
    return '#6e9cf5' if t else '#9aa0b3'


QSS = '''
QMainWindow,QDialog,QWidget{background:@bg;color:@tx;font-size:@fs}
QDockWidget{titlebar-close-icon:none;font-weight:600}QDockWidget::title{background:@pn;padding:6px 10px;border-bottom:1px solid @ln}
QToolBar{background:@pn;border:0;border-bottom:1px solid @ln;spacing:6px;padding:4px 8px}#gbar{background:@pn;border:0;border-bottom:1px solid @ln}#gbar QWidget{background:transparent}#gsep{color:@ln;background:@ln;max-width:1px}QStatusBar QLabel,QStatusBar QPushButton,QStatusBar QWidget{background:transparent}
QToolButton{background:transparent;border:1px solid transparent;border-radius:7px;padding:6px 9px}QToolButton:hover{border-color:@ac;background:@bg2}
QMenuBar{background:@pn}QMenuBar::item:selected,QMenu::item:selected{background:@ac;color:white}QMenu{background:@pn;border:1px solid @ln}
QPushButton{background:@bg2;border:1px solid @ln;border-radius:8px;padding:6px 12px}QPushButton:hover{border-color:@ac}
QPushButton#pri{background:@ac;border-color:@ac;color:white;font-weight:600}QPushButton:disabled{color:@mu}
QLineEdit,QPlainTextEdit,QComboBox,QListWidget,QTreeWidget{background:@bg2;border:1px solid @ln;border-radius:8px;padding:4px 6px;selection-background-color:@ac}
QLineEdit:focus,QPlainTextEdit:focus{border-color:#6e9cf5}QPlainTextEdit#code,QPlainTextEdit#log{font-family:Consolas,"Cascadia Code",monospace}
QTabWidget::pane{border:1px solid @ln;border-radius:8px;top:-1px}QTabBar::tab{background:transparent;color:@mu;padding:6px 12px;border-radius:7px}QTabBar::tab:selected{background:@bg2;color:@tx}
QTreeWidget::item{padding:3px}QTreeWidget::item:hover,QListWidget::item:hover{background:@pn}QListWidget::item:selected,QTreeWidget::item:selected{background:@ac;color:white}
QGroupBox{border:1px solid @ln;border-radius:10px;margin-top:14px;padding:10px}QGroupBox::title{subcontrol-origin:margin;left:12px;color:@mu}
QStatusBar{background:@pn;border-top:1px solid @ln}QProgressBar{border:1px solid @ln;border-radius:6px;background:@bg2;height:10px}QProgressBar::chunk{background:@ac;border-radius:5px}
QScrollBar:vertical{background:transparent;width:10px}QScrollBar::handle:vertical{background:@ln;border-radius:5px;min-height:24px}QScrollBar::add-line,QScrollBar::sub-line{height:0;width:0}
QScrollBar:horizontal{background:transparent;height:10px}QScrollBar::handle:horizontal{background:@ln;border-radius:5px;min-width:24px}
QToolTip{background:@pn;color:@tx;border:1px solid @ln}QSplitter::handle{background:@ln}
QHeaderView::section{background:@pn;color:@mu;border:0;border-bottom:1px solid @ln;padding:4px 6px}
QScrollArea{border:0}QScrollArea>QWidget>QWidget{background:transparent}
QCheckBox,QRadioButton{spacing:6px}QRadioButton::indicator,QCheckBox::indicator{width:14px;height:14px;border:2px solid @mu;background:transparent}QRadioButton::indicator{border-radius:9px}QCheckBox::indicator{border-radius:4px}QRadioButton::indicator:checked,QCheckBox::indicator:checked{background:@ac;border-color:@ac}QRadioButton::indicator:hover,QCheckBox::indicator:hover{border-color:@ac}QFrame#row{background:@bg2;border:1px solid @ln;border-radius:8px}
QComboBox{min-height:30px;max-height:30px;padding:0 34px 0 10px}QComboBox:editable{padding:0 34px 0 4px}
QComboBox::drop-down{subcontrol-origin:border;subcontrol-position:center right;width:30px;border:0;border-left:1px solid @ln;border-top-right-radius:8px;border-bottom-right-radius:8px;background:@pn}
QComboBox::drop-down:hover{background:@ac}QComboBox::down-arrow{image:url(@arrow);width:12px;height:12px}
QComboBox QAbstractItemView{background:@pn;selection-background-color:@ac}QDialogButtonBox QPushButton{min-width:90px}QMessageBox QPushButton{min-width:170px;padding:6px 20px}
'''


def apply_theme(app: QApplication, ui_px=13):
    app.setStyle('Fusion')
    p = QPalette()
    for role, key in ((QPalette.ColorRole.Window, 'bg'), (QPalette.ColorRole.Base, 'bg2'), (QPalette.ColorRole.Button, 'pn'), (QPalette.ColorRole.Text, 'tx'),
                      (QPalette.ColorRole.WindowText, 'tx'), (QPalette.ColorRole.ButtonText, 'tx'), (QPalette.ColorRole.Highlight, 'ac'), (QPalette.ColorRole.ToolTipBase, 'pn'), (QPalette.ColorRole.ToolTipText, 'tx')):
        p.setColor(role, QColor(C[key]))
    app.setPalette(p)
    try:  # the combo-box arrow follows the theme text color
        import tempfile; from pathlib import Path; from .icons import svg_pixmap
        f = Path(tempfile.gettempdir()) / f"odn_arrow_{C['tx'].lstrip('#')}.png"
        if not f.exists(): svg_pixmap('down', C['tx'], 12, 2.0).save(str(f))
        C['arrow'] = f.as_posix()
    except Exception: C['arrow'] = resource('assets/arrow_down.png').as_posix()
    C['fs'] = f'{int(ui_px)}px'
    app.setStyleSheet(re.sub(r'@(\w+)', lambda m: C[m[1]], QSS))
