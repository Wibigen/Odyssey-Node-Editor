"""Ryujinx helpers: find its data folder, copy the compiled exefs into the mod folder, start the game. No Qt here, so it can be tested alone."""
from .i18n import tr
import fnmatch, json, os, re, shutil, subprocess, sys
from pathlib import Path

TITLE_ID = '0100000000010000'  # Super Mario Odyssey
DEFAULT_FILES = 'subsdk9;main.npdm'  # shown as the default; 'subsdk9' follows CMakeLists.txt while this default (or an empty field) is used
OLD_DEFAULT = 'subsdk*;main.npdm'  # default of v2.5, also treated as automatic


def data_candidates(exe=''):
    """Places where Ryujinx keeps its data (portable mode first, then the per-user folder)."""
    c = []
    if exe: c.append(Path(exe).parent / 'portable')
    if sys.platform.startswith('win'): c.append(Path(os.environ.get('APPDATA') or Path.home() / 'AppData' / 'Roaming') / 'Ryujinx')
    elif sys.platform == 'darwin': c.append(Path.home() / 'Library' / 'Application Support' / 'Ryujinx')
    else: c += [Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'Ryujinx', Path.home() / '.var/app/org.ryujinx.Ryujinx/config/Ryujinx']
    return c


def looks_like_data(p):
    p = Path(p); return p.is_dir() and any((p / n).exists() for n in ('Config.json', 'mods', 'system', 'games', 'bis'))


def detect_data(exe=''):
    """First existing Ryujinx data folder, or '' when none is found (the user must give it)."""
    return next((str(p) for p in data_candidates(exe) if looks_like_data(p)), '')


def mod_dir(cfg):
    """<data>/mods/contents/<title id>/<mod name>"""
    return Path(norm(cfg['ryu_data'])) / 'mods' / 'contents' / TITLE_ID / cfg['ryu_mod'].strip()


def norm(p, nt=None):
    """Make slashes agree with the OS. On Windows every '/' becomes '\\' (a leading '//' or '\\\\' is a network / WSL share and stays one)."""
    p = (p or '').strip().strip('"')
    if (os.name == 'nt') if nt is None else nt: p = p.replace('/', '\\')
    return p


def build_dir(cfg, nt=None):
    """Folder holding the compiled files. With the project in WSL (a Linux path such as /home/me/proj) it is reached from Windows through the \\\\wsl.localhost\\<distro> share."""
    nt = (os.name == 'nt') if nt is None else nt
    raw = (cfg.get('ryu_build') or '').strip().strip('"')
    if not raw:
        proj = (cfg.get('project_dir') or '').strip().strip('"')
        if not proj: return None
        raw = proj.rstrip('/\\') + '/build'
    linux = raw.startswith('/') and not raw.startswith('//')  # one leading slash: a path inside WSL (two = a network share)
    if nt and linux:
        d = cfg.get('wsl_distro') or ''
        if not d:
            from .shells import wsl_distros
            ds = wsl_distros(); d = ds[0] if ds else ''
        if d: return Path('\\\\wsl.localhost\\' + d + raw.replace('/', '\\'))
    return Path(norm(raw, nt))


SUBSDK_RE = re.compile(r'set\s*\(\s*SUBSDK\w*\s+"?(subsdk\d+)"?\s*\)', re.I)


def subsdk_name(folder):
    """Name of the compiled sdk file: read from CMakeLists.txt (next to the build folder): set(SUBSDKX subsdk9); else the first of subsdk9 ... subsdk0 present in the build folder; else subsdk9."""
    folder = Path(folder) if folder else None
    if folder is None: return 'subsdk9'
    try:
        m = SUBSDK_RE.search((folder.parent / 'CMakeLists.txt').read_text('utf-8', 'replace'))
        if m: return m.group(1)
    except OSError: pass
    return next((f'subsdk{i}' for i in range(9, -1, -1) if (folder / f'subsdk{i}').is_file()), 'subsdk9')


def patterns(folder, text):
    """Exact file names / patterns to copy. With the default list, 'subsdk9' follows the number written in CMakeLists.txt."""
    t = (text or '').strip()
    if not t or t in (DEFAULT_FILES, OLD_DEFAULT): t = DEFAULT_FILES.replace('subsdk9', subsdk_name(folder))
    return [x.strip() for x in t.replace(',', ';').split(';') if x.strip()]


def find_files(folder, text):
    """Compiled files to copy, looked up in the build folder (and in its 'deploy' / 'exefs' sub-folders). Only exact matches of the names: no .elf / .json / .specs / .Id."""
    out = {}
    if not folder or not Path(folder).is_dir(): return []
    pats = patterns(folder, text)
    for d in (Path(folder), Path(folder) / 'deploy', Path(folder) / 'exefs'):
        if not d.is_dir(): continue
        for f in sorted(d.iterdir()):
            if f.is_file() and f.name not in out and any(fnmatch.fnmatchcase(f.name, p) for p in pats): out[f.name] = f
    return list(out.values())


def problems(cfg):
    """What is still missing before the game can start (list of short sentences)."""
    p = []
    if not cfg.get('ryu_exe') or not Path(norm(cfg['ryu_exe'])).is_file(): p.append('Ryujinx executable not set (or not found)')
    if not cfg.get('ryu_data') or not Path(norm(cfg['ryu_data'])).is_dir(): p.append('Ryujinx data folder not set (or not found)')
    if not (cfg.get('ryu_mod') or '').strip(): p.append('Mod folder name is empty')
    elif any(c in cfg['ryu_mod'] for c in '\\/:*?"<>|') or cfg['ryu_mod'].strip().strip('.') == '': p.append('Mod folder name contains forbidden characters')
    if not cfg.get('ryu_game') or not Path(norm(cfg['ryu_game'])).is_file(): p.append('Game file (.xci / .nsp / .nca...) not set (or not found)')
    return p


def clean_mod(cfg):
    """Empty the mod folder (<data>/mods/contents/<title id>/<name>) completely before a fresh install. Refuses anything that is not exactly that folder."""
    mod = mod_dir(cfg); contents = (Path(norm(cfg['ryu_data'])) / 'mods' / 'contents' / TITLE_ID)
    name = (cfg.get('ryu_mod') or '').strip()
    if not name or name.strip('.') == '' or os.path.normpath(str(mod.parent)) != os.path.normpath(str(contents)): raise RuntimeError(tr('Refusing to clean {0}: it is not a mod folder inside {1}.', mod, contents))
    if not mod.exists(): return 0
    n = 0
    for x in mod.iterdir():
        n += 1
        if x.is_dir() and not x.is_symlink(): shutil.rmtree(x)
        else: x.unlink()
    return n


def install(cfg):
    """Copy the compiled files into <mod>/exefs. Returns (destination, [copied names]); raises RuntimeError with a readable message."""
    b = build_dir(cfg)
    if b is None or not b.is_dir(): raise RuntimeError(tr('Build folder not found: {0}\nCompile first, or set the build folder in the Ryujinx settings.', b or '(no project folder set)'))
    files = find_files(b, cfg.get('ryu_files'))
    if not files: raise RuntimeError(tr('No compiled file ({0}) found in {1}.\nCompile the project first.', '; '.join(patterns(b, cfg.get('ryu_files'))), b))
    mod = mod_dir(cfg); dest = mod / 'exefs'
    try:
        clean_mod(cfg)
        dest.mkdir(parents=True, exist_ok=True)
        for f in files: shutil.copy2(f, dest / f.name)
    except OSError as e: raise RuntimeError(tr('Could not copy to {0}: {1}', dest, e))
    return dest, [f.name for f in files]


def _jf(cfg): return Path(norm(cfg['ryu_data'])) / 'games' / TITLE_ID / 'mods.json'


def _backup(cfg): return _jf(cfg).with_name('mods.json.odn-backup')


def _entry_name(e):
    nm = next((v for k, v in e.items() if k.lower() == 'name' and isinstance(v, str)), '')
    pth = next((v for k, v in e.items() if k.lower() == 'path' and isinstance(v, str)), '')
    return nm or re.split(r'[\\/]', pth.rstrip('\\/'))[-1]


def disable_others(cfg):
    """Turn every other mod of the game off in Ryujinx's mods.json (<data>/games/<title id>/mods.json), keep ours on. Returns the names switched off.
    The original file is saved once as mods.json.odn-backup (restore_others() puts it back)."""
    contents = Path(norm(cfg['ryu_data'])) / 'mods' / 'contents' / TITLE_ID; ours = cfg['ryu_mod'].strip().lower(); jf = _jf(cfg)
    names = [d.name for d in contents.iterdir() if d.is_dir()] if contents.is_dir() else []
    try:
        raw = json.loads(jf.read_text('utf-8-sig')) if jf.is_file() else {}
        if not isinstance(raw, dict): raise ValueError('unexpected content')
        if not _backup(cfg).exists():
            jf.parent.mkdir(parents=True, exist_ok=True); _backup(cfg).write_text(jf.read_text('utf-8-sig') if jf.is_file() else 'null', 'utf-8')
        key = next((k for k, v in raw.items() if k.lower() == 'mods' and isinstance(v, list)), 'mods'); entries = raw.setdefault(key, [])
        sample = next((e for e in entries if isinstance(e, dict)), {}); kk = lambda w: next((k for k in sample if k.lower() == w), w)
        off, seen = [], set()
        for e in entries:
            if not isinstance(e, dict): continue
            nm = _entry_name(e); seen.add(nm.lower()); ek = next((k for k in e if k.lower() == 'enabled'), 'enabled')
            if nm.lower() == ours: e[ek] = True
            elif e.get(ek, True): e[ek] = False; off.append(nm)
        for nm in names:
            if nm.lower() not in seen and nm.lower() != ours: entries.append({kk('name'): nm, kk('path'): str(contents / nm), kk('enabled'): False}); off.append(nm)
        jf.parent.mkdir(parents=True, exist_ok=True); jf.write_text(json.dumps(raw, indent=2), 'utf-8'); return off
    except (OSError, ValueError) as e: raise RuntimeError(tr('Could not update {0}: {1}', jf, e))


def restore_others(cfg):
    """Put back the mods.json saved before disable_others(). Returns True if something was restored."""
    b, jf = _backup(cfg), _jf(cfg)
    if not b.is_file(): return False
    try:
        txt = b.read_text('utf-8')
        if txt.strip() == 'null': jf.unlink(missing_ok=True)
        else: jf.write_text(txt, 'utf-8')
        b.unlink(); return True
    except OSError as e: raise RuntimeError(tr('Could not restore {0}: {1}', jf, e))


def command(cfg):
    a = [norm(cfg['ryu_exe'])] + (['-f'] if cfg.get('ryu_fullscreen') else [])
    import shlex
    if cfg.get('ryu_args'): a += shlex.split(cfg['ryu_args'], posix=os.name != 'nt')
    return a + [norm(cfg['ryu_game'])]


LAUNCH_LOG = None


def launch_log():
    from .config import DATA
    return DATA / 'ryujinx_launch.log'


def launch(cfg):
    """Start Ryujinx with the game. Returns (command, Popen, log file). Its output goes to a log file and its stdin is closed: a GUI program started from a window-less app
    (the .exe) otherwise inherits invalid console handles, and .NET programs can die silently on them."""
    a = command(cfg); exe = Path(norm(cfg['ryu_exe']))
    log = launch_log()
    try:
        out = open(log, 'wb'); out.write(('$ ' + ' '.join(a) + '\n').encode('utf-8', 'replace')); out.flush()
        kw = {'creationflags': 0x00000200 | 0x08000000} if os.name == 'nt' else {'start_new_session': True}  # new process group, no console window
        p = subprocess.Popen(a, cwd=str(exe.parent), stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT, close_fds=True, **kw)
    except OSError as e: raise RuntimeError(tr('Could not start Ryujinx: {0}', e))
    return a, p, log
