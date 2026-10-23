"""Extract the function catalog from OdysseyDecomp (file_list.yml + headers + demangling)."""
from .i18n import tr
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


def read_file_list(text):
    """every entry of file_list.yml -> (offset, [labels], status). Handles a label given inline, quoted, empty, or as a list of aliases (constructors C1 / C2...)."""
    out, cur, mode = [], None, ''
    def unq(v):
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in '\'"': v = v[1:-1].replace("''", "'") if v[0] == "'" else v[1:-1]
        return v
    for ln in text.replace('\r', '').split('\n'):
        st = ln.strip()
        if st.startswith('- offset:'):
            cur = [int(st.split(':', 1)[1].strip(), 16), [], '']; out.append(cur); mode = ''
        elif cur is None: continue
        elif st.startswith('label:'):
            v = unq(st[6:])
            if v: cur[1].append(v)
            mode = 'label' if not st[6:].strip() else ''
        elif st.startswith('status:'): cur[2] = unq(st[7:]); mode = ''
        elif mode == 'label' and st.startswith('- '):
            v = unq(st[2:])
            if v: cur[1].append(v)
        elif st and not st.startswith('-'): mode = ''
    return [tuple(e) for e in out]


def _depth_split(name, sep='::'):
    out, d, cur, i = [], 0, '', 0
    while i < len(name):
        c = name[i]
        if c in '<(': d += 1
        elif c in '>)': d -= 1
        if d == 0 and name.startswith(sep, i): out.append(cur); cur = ''; i += len(sep); continue
        cur += c; i += 1
    out.append(cur); return out


THUNK = ('non-virtual thunk to ', 'virtual thunk to ', 'covariant return thunk to ', 'guard variable for ', 'vtable for ', 'typeinfo ', 'construction vtable ', 'VTT for ', 'reference temporary ')


def parse_demangled(d):
    """-> (qualified name, argument list or None, return type); never fails: a name that is not a function is returned whole"""
    d = re.sub(r' const(?: volatile)?$', '', d.strip())
    if not d.endswith(')'): return d, None, ''
    depth = 0
    for i in range(len(d) - 1, -1, -1):
        depth += (d[i] == ')') - (d[i] == '(')
        if depth == 0: break
    else: return d, None, ''
    head, args = d[:i].rstrip(), d[i + 1:-1]
    if head.endswith('operator'): head = d[:i + 2] if d[i:i + 2] == '()' else head
    ret = ''
    if not head.startswith(THUNK):
        k = head.find('operator'); end = k if k >= 0 else len(head); dd = 0; cut = -1
        for q in range(end - 1, -1, -1):  # a return type is printed before the name of template functions: split at the last space outside <>()
            c = head[q]; dd += (c in '>)') - (c in '<(')
            if c == ' ' and dd == 0: cut = q; break
        if cut >= 0: ret, head = head[:cut].strip(), head[cut + 1:].strip()
    return head, split_args(args), ret


def extract(cfg, progress=lambda msg: None):
    """Build the catalog from EVERY entry of file_list.yml (the filter only applies when it is not empty), write it to disk and return it."""
    root = Path(cfg['decomp_dir']); fl = root / 'data' / 'file_list.yml'
    if not fl.exists(): raise RuntimeError('data/file_list.yml not found: this folder is not OdysseyDecomp')
    inc = re.compile(cfg.get('filter') or '')
    progress('Reading headers…'); rets, statics, members = {}, set(), set()
    rx = re.compile(r'\s*(?:(?:static|virtual|inline|constexpr|\[\[nodiscard\]\])\s+)*([A-Za-z_][\w:<>,\s\*&]*?)\s+([A-Za-z_]\w*)\(')
    for h in [*root.glob('src/**/*.h'), *root.glob('lib/al/**/*.h')]:
        for l in h.read_text('utf-8', errors='ignore').splitlines():
            m = rx.match(l)
            if m and m[1].strip() not in ('return', 'else', 'delete', 'new', 'case'):
                rets.setdefault(m[2], set()).add(m[1].strip()); (statics if l.lstrip().startswith('static ') else members).add(m[2])
    progress('Reading file_list.yml…')
    ent = []  # (offset, symbol, status)
    for off, labels, st in read_file_list(fl.read_text('utf-8', errors='ignore')):
        for lab in (labels or [f'sub_{off:x}']): ent.append((off, lab, st))
    progress(tr('Demangling {0} symbols…', len(ent)))
    mang = [e[1] for e in ent if e[1].startswith('_Z')]; dem = iter(demangle_all(mang, cfg.get('demangler', '')) if mang else [])
    res, seen = [], set()
    for off, sym, st in ent:
        d = next(dem) if sym.startswith('_Z') else sym
        name, args, rt = parse_demangled(d); key = (off, name, tuple(args or ()))
        if key in seen: continue  # C1 / C2 constructors and other aliases with the same meaning
        seen.add(key)
        if inc.pattern and not inc.match(name): continue
        q = [x for x in _depth_split(name) if x != ''] or [name]; base = q[-1]; bare = lambda x: re.sub(r'<.*', '', x).lstrip('~')
        cls = '::'.join(q[:-1]) if len(q) > 1 and re.sub(r'<.*', '', q[-2])[:1].isupper() and not name.startswith(THUNK) else ''
        stl = st[:1].upper() or 'N'
        if cls and bare(base) == bare(q[-2]):  # constructors are kept (destructors too, as plain functions)
            if base.startswith('~'): res.append(dict(s=sym, o=off, k='m', n=name, c=cls, p=[cls + '*'] + [x for x in (args or []) if x != 'void'], r='void', st=stl)); continue
            res.append(dict(s=sym, o=off, k='c', n=name, c=cls, p=[x for x in (args or []) if x != 'void'], r=cls, st=stl)); continue
        r = rt or (next(iter(rets[bare(base)])) if rets.get(bare(base)) and len(rets[bare(base)]) == 1 else 'void')
        k = '' if not cls else 's' if base in statics and base not in members else 'm' if base in members and base not in statics else ''  # '' = not sure (the editor then guesses from the class name)
        res.append(dict(s=sym, o=off, k=k, n=name, c=cls, p=([cls + '*'] if cls else []) + [x for x in (args or []) if x != 'void'], r=r, st=stl))
    if not res: raise RuntimeError('No function extracted (filter too strict or unsuitable demangler)')
    CATF.write_text(json.dumps(res, separators=(',', ':')), 'utf-8')
    return res
