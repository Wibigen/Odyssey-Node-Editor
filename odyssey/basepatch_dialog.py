"""Dialogs around basepatch.py: offer to add what a plugin needs to the exlaunch project, show its state, remove it again."""
import sys
from pathlib import Path

from PySide6.QtWidgets import QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout

from .basepatch import BasePatch
from .projectpath import find_project
from .icons import bind
from .theme import C


def saved_values(pl):
    """The choices made in the base dialog for this plugin (kept with the editor settings)."""
    from .plugins import MANAGER
    return dict((MANAGER.data or {}).get(pl.id, {}).get('base_settings', {}))


def save_values(pl, values):
    from .plugins import MANAGER
    if MANAGER.data is not None: MANAGER.data.setdefault(pl.id, {})['base_settings'] = dict(values)


TRIED = []  # folders looked at by the last project_root() call (shown when nothing is found)


def project_root(cfg):
    """Folder of the exlaunch project as this program can reach it (see projectpath.py: / and \\, quotes, WSL / MSYS paths, a file or sub folder instead of the root...).
    None when nothing is set. When nothing holds a CMakeLists.txt the first guess is returned, so the messages can show it."""
    if not (cfg.get('project_dir') or cfg.get('main_cpp') or '').strip(): return None
    root, tried = find_project(cfg); TRIED[:] = tried
    return root or (Path(tried[0]) if tried else None)


def _why_not(win):
    QMessageBox.information(win, 'Exlaunch project', 'The path of your exlaunch project is not set (or cannot be reached from here).\n\nOpen Tools > Settings, choose the project folder, then use '
                            'Plugins > Plugin explorer > Dear ImGui > "Base…" to add what the plugin needs.')


def show_report(win, title, rep):
    box = QMessageBox(QMessageBox.Warning if rep.warnings or not rep.ok else QMessageBox.Information, title, rep.lines[0] if rep.lines else 'Done.', QMessageBox.Ok, win)
    box.setDetailedText(rep.text()); box.exec()


def offer(win, pl, why=''):
    """Ask to add the plugin's support files to the project. True when the project is ready afterwards."""
    root = project_root(win.cfg)
    if not root: _why_not(win); return False
    bp = BasePatch(pl, root); st = bp.status()
    if not st['project_ok']: QMessageBox.warning(win, pl.title, 'No CMakeLists.txt found. Folders looked at:\n\n' + '\n'.join(TRIED or [str(root)]) + '\n\nIn Tools > Settings, choose the folder that holds CMakeLists.txt (the root of your exlaunch project). Nothing was changed.'); return False
    if st['ready']: return True
    box = QMessageBox(QMessageBox.Question, pl.title, (why + '\n\n' if why else '') + f'"{pl.title}" needs a few additions to your exlaunch project:\n\n• {len(st["missing"])} file(s) to copy (only the ones your project does not already have)\n'
                      f'• CMakeLists.txt: {len(st["cmake"])} line(s) to add\n\nNothing is overwritten, a backup of CMakeLists.txt is kept, and you can take everything back from the Plugin explorer.\nAdd it now?', QMessageBox.Yes | QMessageBox.No, win)
    box.setDetailedText('Files:\n' + '\n'.join('  ' + m for m in st['missing']) + '\n\nCMakeLists.txt:\n' + '\n'.join('  ' + m for m in st['cmake'])); box.setButtonText(QMessageBox.Yes, 'Add to my project'); box.setButtonText(QMessageBox.No, 'Not now')
    if box.exec() != QMessageBox.Yes: return False
    rep = bp.apply(saved_values(pl)); show_report(win, pl.title, rep); return rep.ok and bp.status()['ready']


def offer_remove(win, pl):
    """After a plugin was disabled: offer to take its additions out of the project again (only when it had added some)."""
    root = project_root(win.cfg)
    if not root: return
    bp = BasePatch(pl, root)
    if not bp.manifest.is_file(): return
    if QMessageBox.question(win, pl.title, f'"{pl.title}" is now disabled.\n\nAlso remove what it added to your exlaunch project (files and CMake lines)? '
                            'Files you edited yourself are kept.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes: show_report(win, pl.title, bp.revert())


def check_graph(win, graph):
    """Before the code is written: the graph uses nodes of plugins that need project additions which are missing -> offer them. Returns nothing (writing goes on either way)."""
    from .plugins import MANAGER
    used = {str(n.f.get('pid', '')).replace(':', '.').split('.')[0] for n in graph.nodes.values() if n.type == 'plug'}
    for pl in MANAGER.plugins:
        if pl.enabled and pl.base and pl.id in used and project_root(win.cfg):
            bp = BasePatch(pl, project_root(win.cfg))
            if bp.is_project() and not bp.status()['ready']: offer(win, pl, f'Your graph uses "{pl.title}" nodes.')


class BaseDialog(QDialog):
    """State of a plugin's additions in the project, with Add / Repair and Remove."""

    def __init__(self, win, pl):
        super().__init__(win); self.win, self.pl = win, pl; self.setWindowTitle(f'{pl.title}: exlaunch base'); self.resize(660, 580); v = QVBoxLayout(self)
        t = QLabel((pl.base or {}).get('title') or f'{pl.title} on the exlaunch base'); t.setStyleSheet('font-size:16px;font-weight:600'); v.addWidget(t)
        self.where = QLabel(); self.where.setWordWrap(True); self.where.setStyleSheet(f"color:{C['mu']}"); v.addWidget(self.where)
        self.state = QLabel(); self.state.setWordWrap(True); v.addWidget(self.state); self.build_settings(v); self.txt = QPlainTextEdit(); self.txt.setReadOnly(True); v.addWidget(self.txt, 1)
        info = QLabel('Files are copied only when your project does not have them (nothing is overwritten). CMakeLists.txt gets one marked block and a backup (CMakeLists.txt.odn-backup). '
                      '"Remove" takes back exactly what was added.'); info.setWordWrap(True); info.setStyleSheet(f"color:{C['mu']}"); v.addWidget(info)
        row = QHBoxLayout(); self.bApply, self.bRemove, self.bCfg = QPushButton('Add to my project'), QPushButton('Remove from my project'), QPushButton('Editor settings…')
        self.bApply.setObjectName('pri'); bind(self.bApply, 'plus', '#ffffff', 16); bind(self.bRemove, 'trash', size=16); bind(self.bCfg, 'settings', size=16)
        for b in (self.bApply, self.bRemove, self.bCfg): row.addWidget(b)
        row.addStretch(1); close = QPushButton('Close'); close.clicked.connect(self.accept); row.addWidget(close); v.addLayout(row)
        self.bApply.clicked.connect(self.apply); self.bRemove.clicked.connect(self.remove); self.bCfg.clicked.connect(lambda: (self.win.configure(), self.refresh())); self.refresh()

    # ---- choices written into the generated header ----
    def build_settings(self, v):
        self.fields, self.combos, st = [], {}, (self.pl.base or {}).get('settings')
        self.box = None
        if not (isinstance(st, dict) and st.get('fields') and st.get('file')): return
        self.fields = st['fields']; vals = BasePatch(self.pl, '.').setting_values(saved_values(self.pl))
        self.box = QGroupBox(st.get('title') or 'Settings'); f = QFormLayout(self.box)
        for fl in self.fields:
            cb = QComboBox(); [cb.addItem(str(o[1]), str(o[0])) for o in fl.get('options', [])]; cb.setCurrentIndex(max(0, cb.findData(vals.get(fl['id'])))); cb.currentIndexChanged.connect(self.settings_changed)
            self.combos[fl['id']] = cb; f.addRow(fl.get('label', fl['id']), cb)
        self.note = QLabel(); self.note.setWordWrap(True); self.note.setStyleSheet(f"color:{C['mu']}"); f.addRow(self.note); v.addWidget(self.box); self.update_enabled()

    def values(self):
        return {k: cb.currentData() for k, cb in self.combos.items()}

    def update_enabled(self):
        vals = self.values()
        for fl in self.fields:
            cond = fl.get('enabled_if') or {}; self.combos[fl['id']].setEnabled(all(vals.get(k) == str(x) for k, x in cond.items()))

    def settings_changed(self, *_):
        vals = self.values(); self.update_enabled(); save_values(self.pl, vals); root = project_root(self.win.cfg); msg = 'Saved. It is written into your project when you add the plugin to it.'
        if root:
            bp = BasePatch(self.pl, root)
            if bp.is_project() and bp.manifest.is_file():
                try: msg = f'Written to {bp.write_config(vals)}. Rebuild your mod (make) for it to take effect.'
                except Exception as e: msg = f'Could not write the file: {e}'
        self.note.setText(msg)

    def refresh(self):
        root = project_root(self.win.cfg); self.bApply.setEnabled(False); self.bRemove.setEnabled(False)
        if not root: self.where.setText('Project: (not set)'); self.state.setText('Set your exlaunch project in Settings first.'); self.txt.clear(); return
        bp = BasePatch(self.pl, root); st = bp.status(); self.where.setText(f'Project: {root}')
        if not st['project_ok']: self.state.setText(f'<span style="color:{C["ko"]}">No CMakeLists.txt found: set the project root in Settings.</span>'); self.txt.setPlainText('Folders looked at:\n' + '\n'.join('  ' + t for t in TRIED)); return
        if st['ready']: self.state.setText(f'<span style="color:{C["ok"]}">Ready: everything {self.pl.title} needs is in your project.</span>' + (' (added by this editor)' if st['applied'] else ' (it was already there)'))
        else: self.state.setText(f'<span style="color:{C["warn"]}">{len(st["missing"])} file(s) and {len(st["cmake"])} CMake line(s) are missing.</span>')
        self.txt.setPlainText(('Missing files:\n' + '\n'.join('  ' + m for m in st['missing']) + '\n\n' if st['missing'] else '') + ('Missing in CMakeLists.txt:\n' + '\n'.join('  ' + m for m in st['cmake']) + '\n\n' if st['cmake'] else '')
                              + ('Files added by this editor:\n' + '\n'.join('  ' + m for m in bp.load_manifest().get('added', [])) if st['applied'] else ''))
        self.bApply.setEnabled(not st['ready']); self.bApply.setText('Repair' if st['applied'] else 'Add to my project'); self.bRemove.setEnabled(st['applied'])

    def apply(self):
        root = project_root(self.win.cfg)
        if root: show_report(self, self.pl.title, BasePatch(self.pl, root).apply(saved_values(self.pl)))
        self.refresh()

    def remove(self):
        root = project_root(self.win.cfg)
        if root and QMessageBox.question(self, self.pl.title, 'Remove what this plugin added to your project (files and CMake lines)?') == QMessageBox.Yes: show_report(self, self.pl.title, BasePatch(self.pl, root).revert())
        self.refresh()
