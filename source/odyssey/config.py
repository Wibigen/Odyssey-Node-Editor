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
NOWIN = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

DEFAULTS = dict(decomp_dir='', project_dir='', main_cpp='', build_cmd='cmake --build build', build_env='', wsl_distro='', demangler='',
                filter=r'^(al|rs)::|^(StageScene|PlayerActorHakoniwa|GameDataFunction|PlayerFunction)::')


def load_config():
    try: return {**DEFAULTS, **json.loads(CFGF.read_text('utf-8'))}
    except Exception: return dict(DEFAULTS)


def save_config(cfg):
    CFGF.write_text(json.dumps(cfg, indent=1), 'utf-8')


def main_cpp_path(cfg):
    """Generated file: explicit field, otherwise <project>/src/program/main.cpp."""
    return cfg['main_cpp'] or (str(Path(cfg['project_dir']) / 'src' / 'program' / 'main.cpp') if cfg['project_dir'] else '')


def decomp_ok(cfg):
    return bool(cfg['decomp_dir']) and (Path(cfg['decomp_dir']) / 'data' / 'file_list.yml').exists()


def load_catalog():
    try: return json.loads(CATF.read_text('utf-8'))
    except Exception: return []
