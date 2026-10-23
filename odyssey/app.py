"""Application entry point."""
import sys
from PySide6.QtWidgets import QApplication

from .mainwindow import MainWindow, app_icon
from .config import load_config
from .theme import apply_theme, set_theme
from .plugins import MANAGER


def main():
    if sys.platform == 'win32':  # own taskbar identity so the logo shows instead of Python's
        try:
            import ctypes; ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Wibigen.OdysseyNodes')
        except Exception: pass
    app = QApplication(sys.argv); app.setApplicationName('Odyssey Node Editor')
    try:
        cfg = load_config(); MANAGER.load_all(cfg.get('plugins_disabled', []), enabled=cfg.get('plugins_enabled', []), data=cfg.setdefault('plugin_data', {}))  # plugins first: they can add themes
        set_theme(cfg.get('pref_theme', 'dark'), cfg.get('pref_accent', 'Red'))
    except Exception: pass
    apply_theme(app); app.setWindowIcon(app_icon())
    w = MainWindow(); w.show(); return app.exec()
