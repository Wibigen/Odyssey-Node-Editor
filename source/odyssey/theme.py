"""Dark theme (Qt palette + stylesheet) and node / pin colors."""
import re
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

C = dict(bg='#14161c', bg2='#1a1d25', pn='#20242e', node='#232834', ln='#2f3441', grid='#242834', tx='#e9ebf1', mu='#8a91a5', ac='#e8484f', ok='#4ecb8a', ko='#ef5b5b')
GREEN, ORANGE, TEAL, BLUE, PURPLE = '#4f9a4f', '#c46a2d', '#14a3a3', '#3a7bd5', '#9a66e8'
HEAD_COLORS = dict(hook='#e8484f', func=PURPLE, callfn=PURPLE, callgame='#2fa66a', if_=BLUE, switch=BLUE, **{'for': BLUE, 'while': BLUE, 'ret': BLUE, 'if': BLUE},
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
QMainWindow,QDialog,QWidget{background:@bg;color:@tx;font-size:13px}
QDockWidget{titlebar-close-icon:none;font-weight:600}QDockWidget::title{background:@pn;padding:6px 10px;border-bottom:1px solid @ln}
QToolBar{background:@pn;border:0;border-bottom:1px solid @ln;spacing:4px;padding:4px}
QToolButton{background:transparent;border:1px solid transparent;border-radius:7px;padding:5px 9px}QToolButton:hover{border-color:@ac}
QMenuBar{background:@pn}QMenuBar::item:selected,QMenu::item:selected{background:@ac;color:white}QMenu{background:@pn;border:1px solid @ln}
QPushButton{background:@bg2;border:1px solid @ln;border-radius:8px;padding:6px 12px}QPushButton:hover{border-color:@ac}
QPushButton#pri{background:@ac;border-color:@ac;color:white;font-weight:600}QPushButton:disabled{color:@mu}
QLineEdit,QPlainTextEdit,QComboBox,QListWidget,QTreeWidget{background:@bg2;border:1px solid @ln;border-radius:8px;padding:4px 6px;selection-background-color:@ac}
QLineEdit:focus,QPlainTextEdit:focus{border-color:#6e9cf5}QPlainTextEdit#code,QPlainTextEdit#log{font-family:Consolas,"Cascadia Code",monospace;font-size:12px}
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
QComboBox QAbstractItemView{background:@pn;selection-background-color:@ac}QDialogButtonBox QPushButton{min-width:90px}
'''


def apply_theme(app: QApplication):
    app.setStyle('Fusion')
    p = QPalette()
    for role, key in ((QPalette.ColorRole.Window, 'bg'), (QPalette.ColorRole.Base, 'bg2'), (QPalette.ColorRole.Button, 'pn'), (QPalette.ColorRole.Text, 'tx'),
                      (QPalette.ColorRole.WindowText, 'tx'), (QPalette.ColorRole.ButtonText, 'tx'), (QPalette.ColorRole.Highlight, 'ac'), (QPalette.ColorRole.ToolTipBase, 'pn'), (QPalette.ColorRole.ToolTipText, 'tx')):
        p.setColor(role, QColor(C[key]))
    app.setPalette(p)
    app.setStyleSheet(re.sub(r'@(\w+)', lambda m: C[m[1]], QSS))
