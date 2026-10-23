"""Your function library: save a function (or a selection of nodes) as a .odnf file and insert it again later (templates)."""
import json, re
from pathlib import Path

from .config import LIBDIR
from .graph import E
from .plugnodes import EMBED, plug_def

EXT = '.odnf'


def collect(g, ids, expand=True):
    """Node ids to save. expand=True follows a function / hook completely (its whole flow, the values it uses, the functions it calls, the globals it reads);
    expand=False keeps exactly the given nodes."""
    ids, out, stack = set(ids), set(), list(ids)
    if not expand: return {i for i in ids if i in g.nodes}
    gl = {n.f.get('name'): n.id for n in g.nodes.values() if n.type == 'global'}
    while stack:
        i = stack.pop()
        if i in out or i not in g.nodes: continue
        out.add(i); n = g.nodes[i]
        for e in g.edges:
            if e[0][0] == i and g.pin_type(i, e[0][1], 'o') == E: stack.append(e[1][0])
            if e[1][0] == i and g.pin_type(i, e[1][1], 'i') != E: stack.append(e[0][0])
        if n.type == 'callfn' and g.fn(n): stack.append(g.fn(n).id)
        for key in ('variable', 'name'):
            if n.type in ('getvar', 'setvar') and n.f.get(key) in gl: stack.append(gl[n.f[key]])
    return out


def fragment(g, ids, name, desc=''):
    ids = {i for i in ids if i in g.nodes}; pids = {g.nodes[i].f.get('pid') for i in ids if g.nodes[i].type == 'plug'}
    return dict(format='odnf', version=1, name=name, desc=desc, inc=g.inc, plug={p: plug_def(p) for p in pids if plug_def(p)},
                nodes={str(i): dict(id=i, type=g.nodes[i].type, f=g.nodes[i].f, d=g.nodes[i].d, x=g.nodes[i].x, y=g.nodes[i].y) for i in sorted(ids)},
                edges=[[list(e[0]), list(e[1])] for e in g.edges if e[0][0] in ids and e[1][0] in ids],
                groups=[dict(name=v['name'], color=v['color'], nodes=[i for i in v['nodes'] if i in ids]) for v in g.groups.values() if any(i in ids for i in v['nodes'])])


def safe_name(name): return re.sub(r'[^\w\- ]+', '_', name).strip() or 'function'


def save(g, ids, name, desc='', expand=True):
    """-> path of the written file (an existing file with the same name is replaced)"""
    frag = fragment(g, collect(g, ids, expand), name, desc); p = LIBDIR / (safe_name(name) + EXT)
    p.write_text(json.dumps(frag, indent=1), 'utf-8'); return p


def entries():
    """[(path, name, description, number of nodes)] sorted by name"""
    out = []
    for p in sorted(LIBDIR.glob('*' + EXT)):
        try: j = json.loads(p.read_text('utf-8')); out.append((p, j.get('name') or p.stem, j.get('desc', ''), len(j.get('nodes', {}))))
        except Exception: pass
    return sorted(out, key=lambda t: t[1].lower())


def load(path): return json.loads(Path(path).read_text('utf-8'))


def insert(g, frag, x=0.0, y=0.0):
    """Add a saved fragment to graph g with fresh ids at (x, y); it is wrapped in a group named after the fragment.
    Returns (new ids, notes about renamed or reused things)."""
    notes, mapping, new = [], {}, []
    for p, d in (frag.get('plug') or {}).items():  # nodes of a plugin: keep working even if the plugin is not installed here
        if not plug_def(p) and isinstance(d, dict) and 'template' in d and 'fields' in d: EMBED[p] = d; notes.append(f'plugin node {d.get("label", p)} uses the copy saved with the function (plugin not installed)')
    have_fn = {n.f.get('name') for n in g.nodes.values() if n.type == 'func'}; have_gl = {n.f.get('name'): n.id for n in g.nodes.values() if n.type == 'global'}
    nodes = {int(k): v for k, v in frag['nodes'].items()}; ren = {}
    for k, v in nodes.items():  # name clashes
        if v['type'] == 'func' and v['f'].get('name') in have_fn:
            old, base, c = v['f']['name'], v['f']['name'], 2
            while f'{base}_{c}' in have_fn: c += 1
            ren[old] = f'{base}_{c}'; have_fn.add(ren[old]); notes.append(f'function {old} renamed to {ren[old]} (name already used)')
    minx, miny = min([v['x'] for v in nodes.values()] or [0]), min([v['y'] for v in nodes.values()] or [0])
    for k, v in nodes.items():
        f = dict(v['f'])
        if v['type'] == 'global' and f.get('name') in have_gl: mapping[k] = have_gl[f['name']]; notes.append(f'global {f["name"]} already exists: reused'); continue
        if v['type'] == 'func' and f.get('name') in ren: f['name'] = ren[f['name']]
        if v['type'] == 'callfn' and f.get('name') in ren: f['name'] = ren[f['name']]
        n = g.add(v['type'], f, x + v['x'] - minx, y + v['y'] - miny, v.get('d')); mapping[k] = n.id; new.append(n.id)
    for a, b in frag.get('edges', []):
        if a[0] in mapping and b[0] in mapping:
            e = ((mapping[a[0]], a[1]), (mapping[b[0]], b[1]))
            if e not in g.edges: g.edges.append(e)
    have = set(g.inc.split('\n'))
    add = [ln for ln in (frag.get('inc') or '').split('\n') if ln.strip() and ln not in have]
    if add: g.inc = g.inc.rstrip('\n') + '\n' + '\n'.join(add); notes.append(f'{len(add)} include line(s) added')
    if frag.get('groups'):
        for gr in frag['groups']:
            members = [mapping[i] for i in gr['nodes'] if i in mapping and mapping[i] in new]
            if members: g.make_group(members, gr['name'], gr.get('color', ''))
    elif new: g.make_group(new, frag.get('name') or 'Imported function')
    return new, notes
