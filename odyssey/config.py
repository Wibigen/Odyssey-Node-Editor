"""Paths and persistent settings (JSON in %APPDATA%/OdysseyNodes)."""
import json, os, subprocess
from pathlib import Path

import sys


def resource(name):
    """Path of a bundled file (works from source and from the PyInstaller exe)."""
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
    return base / name


DATA = Path(os.environ.get('APPDATA') or Path.home() / '.config') / 'OdysseyNodes'
DATA.mkdir(parents=True, exist_ok=True)
CFGF, CATF, GRAPHF = DATA / 'config.json', DATA / 'catalog.json', DATA / 'graph.json'
STARTF = DATA / 'startup.odn'  # graph used by File > New
LIBDIR = DATA / 'library'      # your saved functions (.odnf)
LIBDIR.mkdir(parents=True, exist_ok=True)
NOWIN = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

DEFAULTS = dict(decomp_dir='', project_dir='', main_cpp='', build_cmd='cmake --build build', build_env='', wsl_distro='', demangler='',
                plugins_disabled=[], plugins_enabled=[], plugin_data={}, tour_done=False, shortcuts={}, filter=r'^(al|rs)::|^(StageScene|PlayerActorHakoniwa|GameDataFunction|PlayerFunction)::', ret_overrides={}, favorites=[],
                # preferences
                pref_startup='session', pref_autosave=True, pref_grid=True, pref_snap=False, pref_code_size=10, pref_wrap=False, pref_highlight=True, pref_ui_size=13, pref_confirm_new=True, pref_install='symbol', pref_new='startup', pref_links_top=False, pref_autogroup=True, pref_theme='dark', pref_accent='Red', pref_dropmenu=True, pref_linenumbers=True, pref_calls='direct',
                # Ryujinx tab
                ryu_exe='', ryu_data='', ryu_game='', ryu_mod='MyOdysseyMod', ryu_build='', ryu_files='', ryu_args='', ryu_fullscreen=False, ryu_install_first=True, ryu_disable_others=True, ryu_compile_first=False)


def load_config():
    try: return {**DEFAULTS, **json.loads(CFGF.read_text('utf-8'))}
    except Exception: return dict(DEFAULTS)


def save_config(cfg):
    CFGF.write_text(json.dumps(cfg, indent=1), 'utf-8')


MAIN_CANDIDATES = (('src', 'program', 'main.cpp'), ('src', 'main.cpp'))


def main_cpp_candidates(project):
    """Where an exlaunch main.cpp can live (the template uses src/program/, some forks use src/)."""
    return [str(Path(project).joinpath(*c)) for c in MAIN_CANDIDATES] if project else []


def main_cpp_path(cfg):
    """Generated file: explicit field, else the first existing <project>/src/program/main.cpp or <project>/src/main.cpp, else the first one."""
    if cfg['main_cpp']: return cfg['main_cpp']
    c = main_cpp_candidates(cfg['project_dir'])
    return next((p for p in c if Path(p).is_file()), next((p for p in c if Path(p).parent.is_dir()), c[0] if c else ''))


def decomp_ok(cfg):
    return bool(cfg['decomp_dir']) and (Path(cfg['decomp_dir']) / 'data' / 'file_list.yml').exists()


def load_catalog():
    try: return json.loads(CATF.read_text('utf-8'))
    except Exception: return []
