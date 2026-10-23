"""Finds the exlaunch project folder from what the user typed in Settings (Qt-independent).

Handles: quotes and spaces, ~ and %VARS%, / and \\ mixed, a file path (main.cpp) or a sub folder (src/program) instead of the root,
\\\\wsl$\\ and \\\\wsl.localhost\\ (both spellings), a Linux path (/home/me/mod) when the build runs in WSL, MSYS / Git Bash paths (/c/Users/me/mod),
and a parent folder that holds a single project.
"""
import os, re
from pathlib import Path

from .shells import UNC

MSYS = re.compile(r'^/([a-zA-Z])(?:/(.*))?$')
WINDRIVE = re.compile(r'^[a-zA-Z]:')


def clean(p):
    p = (p or '').strip().strip('"\'').strip()
    return os.path.expandvars(os.path.expanduser(p)) if p else ''


def cmake_file(d):
    """<d>/CMakeLists.txt (any capitalisation) or None."""
    try:
        d = Path(d)
        f = d / 'CMakeLists.txt'
        if f.is_file(): return f
        if d.is_dir():
            for x in d.iterdir():
                if x.name.lower() == 'cmakelists.txt' and x.is_file(): return x
    except OSError: pass
    return None


def variants(p, cfg, distros=()):
    """Every way the typed path could point to the project, most likely first (strings)."""
    p = clean(p)
    if not p: return []
    out = []
    add = lambda s: out.append(s) if s and s not in out else None
    nt = os.name == 'nt'
    if not nt:
        add(p.replace('\\', '/') if WINDRIVE.match(p) else p); return out
    fwd = p.replace('\\', '/')
    if fwd.startswith('//'):  # \\wsl$\Ubuntu\x  <->  \\wsl.localhost\Ubuntu\x
        win = '\\\\' + fwd[2:].replace('/', '\\'); add(win); m = UNC.match(win)
        if m:
            for host in ('wsl.localhost', 'wsl$'): add(f'\\\\{host}\\{m.group(1)}{m.group(2)}')
        return out
    if fwd.startswith('/'):  # Linux path (WSL) or MSYS / Git Bash path (/c/Users/me/mod)
        ms = MSYS.match(fwd); d = (cfg.get('wsl_distro') or '').strip(); wsl = cfg.get('build_env') == 'wsl'
        drive = (lambda: add(f'{ms.group(1).upper()}:\\' + (ms.group(2) or '').replace('/', '\\'))) if ms else (lambda: None)
        if not wsl: drive()
        for name in ([d] if d else []) + [x for x in distros if x != d]:
            for host in ('wsl.localhost', 'wsl$'): add(f'\\\\{host}\\{name}' + fwd.replace('/', '\\'))
        if wsl: drive()
        add(fwd.replace('/', '\\')); return out
    add(fwd.replace('/', '\\')); return out


_DISTROS = []


def find_project(cfg, distros=None):
    """-> (root Path or None, tried [str]). Looks at project_dir, then at the folder of main_cpp; walks up from a file or sub folder, and down one level."""
    tried, found = [], None
    if distros is None:
        distros = ()
        if os.name == 'nt' and (cfg.get('build_env') in ('wsl', '') or True):
            p = clean(cfg.get('project_dir'))
            if p.startswith('/') and not (cfg.get('wsl_distro') or '').strip():
                from .shells import wsl_distros
                if not _DISTROS: _DISTROS.extend(wsl_distros())
                distros = tuple(_DISTROS)
    for key in ('project_dir', 'main_cpp'):
        for v in variants(cfg.get(key), cfg, distros):
            q = Path(v)
            try: base = q.parent if q.is_file() else q
            except OSError: base = q
            tried.append(str(base))
            chain = [base] + list(base.parents)[:5]
            for d in chain:
                if cmake_file(d): found = d; break
            if found: break
            try:  # the typed folder holds the project one level down
                subs = [x for x in base.iterdir() if x.is_dir() and cmake_file(x)] if base.is_dir() else []
                if len(subs) == 1: found = subs[0]; break
            except OSError: pass
        if found: break
    return found, tried
