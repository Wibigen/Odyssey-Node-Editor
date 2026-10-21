"""Extract the function catalog from OdysseyDecomp (file_list.yml + headers + demangling)."""
import json, os, re, shutil, subprocess
from pathlib import Path
from .config import CATF, NOWIN


def find_demangler(custom=''):
    c = [custom] + [shutil.which(x) for x in ('aarch64-none-elf-c++filt', 'llvm-cxxfilt', 'c++filt')]
    for d in (os.environ.get('DEVKITPRO'), 'C:/devkitPro', '/opt/devkitpro'):  # devkitA64 is required by exlaunch
        if d: c.append(shutil.which('aarch64-none-elf-c++filt', path=str(Path(d) / 'devkitA64' / 'bin')))
    return next((x for x in c if x and Path(x).exists()), None)


def demangle_all(syms, custom=''):
    exe = find_demangler(custom)
    if exe:
        p = subprocess.run([exe], input='\n'.join(syms) + '\n', capture_output=True, text=True, encoding='utf-8', errors='replace', creationflags=NOWIN)
        out = p.stdout.split('\n')[:len(syms)]
        if len(out) == len(syms): return out
    try:
        import cxxfilt
        def d(s):
            try: return cxxfilt.demangle(s)
            except Exception: return s
        return [d(s) for s in syms]
    except ImportError:
        raise RuntimeError('No demangler found: install devkitPro (aarch64-none-elf-c++filt) or LLVM (llvm-cxxfilt), or set its path in Advanced.')


def split_args(s):
    o, d, c = [], 0, ''
    for ch in s:
        d += ch in '<('; d -= ch in '>)'
        if ch == ',' and d == 0: o.append(c.strip()); c = ''
        else: c += ch
    if c.strip(): o.append(c.strip())
    return o


def extract(cfg, progress=lambda msg: None):
    """Build the catalog, write it to disk and return it. Raises RuntimeError on failure."""
    root = Path(cfg['decomp_dir']); fl = root / 'data' / 'file_list.yml'
    if not fl.exists(): raise RuntimeError('data/file_list.yml not found: this folder is not OdysseyDecomp')
    inc = re.compile(cfg['filter'])
    progress('Reading headers…'); rets = {}
    rx = re.compile(r'\s*(?:(?:static|virtual|inline|constexpr|\[\[nodiscard\]\])\s+)*([A-Za-z_][\w:<>,\s\*&]*?)\s+([A-Za-z_]\w*)\(')
    for h in [*root.glob('src/**/*.h'), *root.glob('lib/al/**/*.h')]:
        for l in h.read_text('utf-8', errors='ignore').splitlines():
            m = rx.match(l)
            if m and m[1].strip() not in ('return', 'else', 'delete', 'new', 'case'): rets.setdefault(m[2], set()).add(m[1].strip())
    progress('Reading file_list.yml…')
    txt = fl.read_text('utf-8', errors='ignore').replace('\r', '')
    ent = [(int(o, 16), s, st) for o, _, s, st in re.findall(r'offset: (0x[0-9a-f]+)\n\s+size: (\d+)\n\s+label: (\S+)\n\s+status: (\w+)', txt) if s.startswith('_ZN')]
    progress(f'Demangling {len(ent)} symbols…')
    res = []
    for (off, sym, st), d in zip(ent, demangle_all([e[1] for e in ent], cfg.get('demangler', ''))):
        d = re.sub(r' const$', '', d); m = re.match(r'^([\w:]+)\((.*)\)$', d)
        if not m or not inc.match(m[1]): continue
        q = m[1].split('::'); name = q[-1]
        cls = '::'.join(q[:-1]) if len(q) > 1 and q[-2][:1].isupper() else ''  # capitalised = class (heuristic)
        if cls and name.lstrip('~') == q[-2]: continue  # ctor/dtor
        r = rets.get(name); r = next(iter(r)) if r and len(r) == 1 else 'void'
        res.append(dict(s=sym, o=off, n='::'.join(q), c=cls, p=([cls + '*'] if cls else []) + [x for x in split_args(m[2]) if x != 'void'], r=r, st=st[0]))
    if not res: raise RuntimeError('No function extracted (filter too strict or unsuitable demangler)')
    CATF.write_text(json.dumps(res, separators=(',', ':')), 'utf-8')
    return res
