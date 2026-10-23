"""Vector icons (24x24, outline style) drawn from SVG paths with the colors of the current theme. No image files."""
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from .theme import C

P = {
    'new': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M12 12v6M9 15h6"/>',
    'open': '<path d="M3 6a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    'save': '<path d="M5 3h11l4 4v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M7 3v6h8V3"/><path d="M7 21v-7h10v7"/>',
    'undo': '<path d="M9 14L4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
    'redo': '<path d="M15 14l5-5-5-5"/><path d="M20 9H9.5a5.5 5.5 0 0 0 0 11H13"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'func': '<path d="M12 5v14M5 12h14"/><rect x="3" y="3" width="18" height="18" rx="4"/>',
    'group': '<rect x="3" y="3" width="18" height="18" rx="2" stroke-dasharray="4 3"/><rect x="8" y="8" width="8" height="8" rx="1"/>',
    'note': '<path d="M4 4h16v10l-6 6H4z"/><path d="M14 20v-6h6"/>',
    'fit': '<path d="M8 3H5a2 2 0 0 0-2 2v3M16 3h3a2 2 0 0 1 2 2v3M8 21H5a2 2 0 0 1-2-2v-3M16 21h3a2 2 0 0 0 2-2v-3"/>',
    'trash': '<path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6M10 11v6M14 11v6"/>',
    'library': '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/>',
    'settings': '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    'globe': '<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    'search': '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    'up': '<path d="M6 15l6-6 6 6"/>', 'down': '<path d="M6 9l6 6 6-6"/>',
    'x': '<path d="M18 6L6 18M6 6l12 12"/>',
    'star': '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.3-6.2 3.3L7 14.2 2 9.3l6.9-1z"/>',
    'star_fill': '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.3-6.2 3.3L7 14.2 2 9.3l6.9-1z"/>',
    'link': '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><path d="M15 3h6v6M10 14L21 3"/>',
    'play_fill': '<path d="M7 4l13 8-13 8z"/>', 'stop_fill': '<rect x="5" y="5" width="14" height="14" rx="2"/>',
    'wrench': '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
    'write': '<path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>',
    'copy': '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1"/>',
    'warn': '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    'error': '<circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/>',
    'info': '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
    'ok': '<circle cx="12" cy="12" r="10"/><path d="M8 12l3 3 5-6"/>',
    'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    'moon': '<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/>',
    'palette': '<circle cx="13.5" cy="6.5" r="1"/><circle cx="17.5" cy="10.5" r="1"/><circle cx="8.5" cy="7.5" r="1"/><circle cx="6.5" cy="12.5" r="1"/><path d="M12 2a10 10 0 0 0 0 20c1.1 0 2-.9 2-2 0-.5-.2-1-.5-1.3-.3-.3-.5-.8-.5-1.3 0-1.1.9-2 2-2H18a4 4 0 0 0 4-4c0-5-4.5-9-10-9z"/>',
    'help': '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01"/>',
}
_cache, _bound = {}, []


def svg_pixmap(name, color, size, dpr=2.0):
    key = (name, color, size)
    if key in _cache: return _cache[key]
    fill = color if name.endswith('_fill') else 'none'
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{fill}" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{P[name]}</svg>'
    px = int(size * dpr); img = QImage(px, px, QImage.Format_ARGB32_Premultiplied); img.fill(Qt.transparent)
    p = QPainter(img); QSvgRenderer(QByteArray(svg.encode())).render(p); p.end()
    pm = QPixmap.fromImage(img); pm.setDevicePixelRatio(dpr); _cache[key] = pm; return pm


def icon(name, color=None, size=18):
    """color: a '#rrggbb' string or a theme key ('tx', 'mu', 'ac'...); default = the theme text color"""
    col = C.get(color, color) if color else C['tx']
    ic = QIcon(); ic.addPixmap(svg_pixmap(name, col, size)); dis = C['mu']; ic.addPixmap(svg_pixmap(name, dis, size), QIcon.Disabled); return ic


def bind(widget, name, color=None, size=18):
    """set the icon of a button / action now, and again whenever the theme changes"""
    _bound.append((widget, name, color, size)); widget.setIcon(icon(name, color, size)); return widget


def refresh():
    _cache.clear(); live = []
    for w, name, color, size in _bound:
        try: w.setIcon(icon(name, color, size)); live.append((w, name, color, size))
        except RuntimeError: pass  # the widget was deleted
    _bound[:] = live
