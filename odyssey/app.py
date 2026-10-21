"""Application entry point."""
import sys
from PySide6.QtWidgets import QApplication

from .mainwindow import MainWindow, app_icon
from .theme import apply_theme


def main():
    if sys.platform == 'win32':  # own taskbar identity so the logo shows instead of Python's
        try:
            import ctypes; ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Wibigen.OdysseyNodes')
        except Exception: pass
    app = QApplication(sys.argv); app.setApplicationName('Odyssey Nodes'); apply_theme(app); app.setWindowIcon(app_icon())
    w = MainWindow(); w.show(); return app.exec()
