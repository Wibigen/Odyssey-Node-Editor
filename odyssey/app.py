"""Application entry point."""
import sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from .mainwindow import MainWindow, app_icon
from .config import load_config
from .theme import apply_theme, set_theme
from .plugins import MANAGER
from . import i18n


def main():
    if sys.platform == 'win32':  # own taskbar identity so the logo shows instead of Python's
        try:
            import ctypes; ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Wibigen.OdysseyNodes')
        except Exception: pass
    app = QApplication(sys.argv); app.setApplicationName('Odyssey Node Editor')
    try: i18n.set_language(load_config().get('language', 'en')); i18n.install_qt(app)
    except Exception: pass
    try:
        cfg = load_config(); MANAGER.load_all(cfg.get('plugins_disabled', []), enabled=cfg.get('plugins_enabled', []), data=cfg.setdefault('plugin_data', {}))  # plugins first: they can add themes
        set_theme(cfg.get('pref_theme', 'dark'), cfg.get('pref_accent', 'Red'))
    except Exception: pass
    apply_theme(app); app.setWindowIcon(app_icon())
    w = MainWindow(); w.show()
    if len(sys.argv) > 1 and Path(sys.argv[1]).is_file(): QTimer.singleShot(300, lambda: w.open_path(sys.argv[1]))  # odyssey_nodes.py my_mod.odn
    rc = app.exec()
    if getattr(w, '_restart', False):  # language changed: start again
        import subprocess
        try: subprocess.Popen(([sys.executable] + sys.argv[1:]) if getattr(sys, 'frozen', False) else ([sys.executable] + sys.argv))
        except Exception: pass
    return rc
