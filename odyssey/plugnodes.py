"""Nodes that come from plugins (Qt-independent).

A plugin describes a node with a small dictionary (JSON in plugin.json / nodes.json, or api.add_node() from Python):

    {"id": "printf", "label": "Print (printf)", "category": "Standard I/O", "description": "...",
     "flow": true,                      # true = statement with execution pins, false (default) = value
     "inputs":  [{"id": "text", "type": "const char*", "label": "text", "default": ""}],
     "repeat":  {"id": "arg", "type": "", "label": "argument", "min": 0, "max": 6, "default": 1},   # optional growing list of inputs
     "output":  {"type": "int", "label": "result"},       # value nodes (and flow nodes that give a result)
     "fields":  [{"key": "fmt", "label": "Format", "kind": "text", "default": "%d"}],   # kinds: text, type, bool, choice
     "template": "printf(@fmt, $text$,arg)",
     "includes": ["<cstdio>"], "helpers": "static int myHelper();", "color": "#c98a2b"}

Template syntax:  @key = value of a field,  $id = value plugged into an input,
$,id = the repeated inputs as ", a, b" (nothing when there are none),  $*id = the repeated inputs as "a, b".
"""
import re

PLUG = {}   # 'plugin.node' -> normalised definition (nodes of the plugins that are loaded)
EMBED = {}  # definitions found inside a graph file or kept from a plugin that was disabled: the graph keeps working without the plugin

KINDS = ('text', 'type', 'bool', 'choice', 'func', 'var')
CATALOG = {}  # plugin id -> dict(title, color, includes, entries=[...], by_id={}): big lists of functions, browsed with Plugins > Plugin function browser
_CAT_CACHE = {}
IDENT = re.compile(r'^[A-Za-z_]\w*$')


def is_loaded(pid):
    """True when the plugin that provides this node is loaded (the node does not rely on a copy saved in the graph)."""
    return pid in PLUG or (isinstance(pid, str) and ':' in pid and pid.split(':', 1)[0] in CATALOG and catalog_def(pid) is not None)


def plug_def(pid):
    return PLUG.get(pid) or EMBED.get(pid) or catalog_def(pid)


def _str(v, d=''):
    return v if isinstance(v, str) else d


def normalise(raw, plugin_id, plugin_title='', color=''):
    """Check a raw node description and fill in the defaults. Raises ValueError with a readable message."""
    if not isinstance(raw, dict): raise ValueError('a node must be an object')
    nid = _str(raw.get('id')).strip()
    if not IDENT.match(nid): raise ValueError(f'node id "{nid}" must be a plain name (letters, digits, _)')
    if not _str(raw.get('template')).strip(): raise ValueError(f'node "{nid}": "template" is missing')
    d = dict(pid=f'{plugin_id}.{nid}', id=nid, plugin=plugin_id, plugin_title=plugin_title or plugin_id, label=_str(raw.get('label')).strip() or nid,
             category=_str(raw.get('category')).strip() or (plugin_title or plugin_id), description=_str(raw.get('description')).strip() or 'Node added by a plugin.',
             flow=bool(raw.get('flow') or raw.get('both')), both=bool(raw.get('both')), place=_str(raw.get('place')) if raw.get('place') in ('main',) else '', template=raw['template'], color=_str(raw.get('color')) or color,
             includes=[_str(i).strip() for i in (raw.get('includes') or []) if _str(i).strip()], helpers=_str(raw.get('helpers')),
             init=[_str(i) for i in (raw.get('init') or []) if _str(i).strip()])
    d['inputs'] = []
    for i in raw.get('inputs') or []:
        k = _str(i.get('id')).strip()
        if not IDENT.match(k): raise ValueError(f'node "{nid}": input id "{k}" is not a plain name')
        d['inputs'].append(dict(id=k, type=_str(i.get('type')), label=_str(i.get('label')) or k, default=_str(i.get('default'))))
    r = raw.get('repeat')
    if r:
        k = _str(r.get('id')).strip()
        if not IDENT.match(k): raise ValueError(f'node "{nid}": repeat id "{k}" is not a plain name')
        lo, hi = max(0, int(r.get('min', 0))), min(32, int(r.get('max', 8)))
        d['repeat'] = dict(id=k, type=_str(r.get('type')), label=_str(r.get('label')) or k, min=lo, max=max(lo, hi), default=min(max(int(r.get('default', lo)), lo), max(lo, hi)),
                           field=_str(r.get('field')) or f'n_{k}')
    out = raw.get('output') or ({'type': '', 'label': 'result'} if not d['flow'] else None)
    d['output'] = dict(type=_str(out.get('type')), label=_str(out.get('label')) or 'result') if out else None
    d['fields'] = []
    for f in raw.get('fields') or []:
        k = _str(f.get('key')).strip()
        if not IDENT.match(k): raise ValueError(f'node "{nid}": field key "{k}" is not a plain name')
        kind = f.get('kind', 'text')
        if kind not in KINDS: raise ValueError(f'node "{nid}": field "{k}" has an unknown kind "{kind}" (use {", ".join(KINDS)})')
        opts = [(str(o[0]), str(o[1])) if isinstance(o, (list, tuple)) else (str(o), str(o)) for o in (f.get('options') or [])]
        d['fields'].append(dict(key=k, label=_str(f.get('label')) or k, kind=kind, options=opts, hint=_str(f.get('hint')), default=f.get('default', False if kind == 'bool' else (opts[0][0] if kind == 'choice' and opts else ''))))
    if d.get('repeat'):
        rp = d['repeat']
        if not any(f['key'] == rp['field'] for f in d['fields']):
            d['fields'].append(dict(key=rp['field'], label=f"Number of {rp['label']}s", kind='choice', options=[(str(n), str(n)) for n in range(rp['min'], rp['max'] + 1)], hint='', default=str(rp['default'])))
    if d['both'] and not d['output']: d['both'] = False
    if d['flow'] and d['output']:  # a flow node that gives a result can keep it in a named variable
        d['fields'].append(dict(key='save', label='Save result as', kind='text', options=[], hint='variable name (optional)', default=''))
    return d


def is_flow(d, f):
    """True when the node has execution pins (a 'both' node loses them when it is used as a value)."""
    return bool(d['flow'] and not d['place'] and not (d['both'] and f.get('inline')))


def defaults(d):
    """Field values of a freshly created node (always carries the node id)."""
    return {'pid': d['pid'], **{f['key']: f['default'] for f in d['fields']}}


def count(d, f):
    """How many repeated inputs the node currently has."""
    r = d.get('repeat')
    if not r: return 0
    try: n = int(str(f.get(r['field'], r['default'])).strip())
    except ValueError: n = r['default']
    return min(max(n, r['min']), r['max'])


def pins(d, f):
    """(inputs, outputs) as (id, type, label) lists, without the execution pins."""
    ins = [(i['id'], i['type'], i['label']) for i in d['inputs']]  # (the execution pins are added by the graph)
    if d.get('repeat'): ins += [(f"{d['repeat']['id']}{k + 1}", d['repeat']['type'], f"{d['repeat']['label']} {k + 1}") for k in range(count(d, f))]
    outs = [('out', d['output']['type'], d['output']['label'])] if d['output'] else []
    return ins, outs


def render(d, f, arg):
    """C++ text of the node. arg(pin id) gives the text plugged into an input."""
    t = d['template']
    keys = sorted((x['key'] for x in d['fields']), key=len, reverse=True)
    if keys: t = re.sub(r'@(' + '|'.join(map(re.escape, keys)) + r')\b', lambda m: str(f.get(m[1], '')), t)
    rid = d['repeat']['id'] if d.get('repeat') else None
    n = count(d, f)

    def sub(m):
        mode, k = m[1], m[2]
        if k == rid and mode in (',', '*'):
            vals = [arg(f'{rid}{i + 1}') for i in range(n)]
            return (', ' if mode == ',' and vals else '') + ', '.join(vals)
        if any(i['id'] == k for i in d['inputs']): return arg(k)
        return m[0]
    return re.sub(r'\$([,*]?)(\w+)', sub, t)


def include_lines(d):
    out = []
    for i in d['includes']:
        out.append(i if i.startswith('#') else (f'#include {i}' if i[0] in '<"' else f'#include <{i}>'))
    return out


# ---------------- function catalogs ----------------
def add_catalog(plugin_id, plugin_title, data, color=''):
    """data = {"title", "includes", "entries": [{"id", "label", "call", "kind": "f|c|m", "r", "p": [[type, name, default]], "c": category, "d": doc, "va": bool}]}"""
    ents = [e for e in (data.get('entries') or []) if isinstance(e, dict) and e.get('id') and e.get('call')]
    CATALOG[plugin_id] = dict(plugin=plugin_id, plugin_title=plugin_title, title=data.get('title') or plugin_title, color=data.get('color') or color, includes=list(data.get('includes') or []),
                              entries=ents, by_id={e['id']: e for e in ents})
    for k in [k for k in _CAT_CACHE if k.startswith(plugin_id + ':')]: del _CAT_CACHE[k]


def clear_catalogs():
    CATALOG.clear(); _CAT_CACHE.clear()


def catalog_def(pid):
    """Node definition built on demand from a catalog entry; pid = 'plugin:entry'. None when unknown."""
    if not isinstance(pid, str) or ':' not in pid: return None
    if pid in _CAT_CACHE: return _CAT_CACHE[pid]
    pl, _, eid = pid.partition(':'); cat = CATALOG.get(pl); e = cat['by_id'].get(eid) if cat else None
    if not e: return None
    kind, ret, params, va = e.get('kind', 'f'), e.get('r') or 'void', e.get('p') or [], bool(e.get('va'))
    ins, seen = [], set()
    if kind == 'm': ins.append(dict(id='self', type=e.get('self') or '', label='object', default=''))
    for i, p in enumerate(params):
        t, nm, dflt = (list(p) + ['', '', ''])[:3]; k = re.sub(r'\W', '_', nm or f'a{i}') or f'a{i}'
        if k[0].isdigit() or k in seen: k = f'a{i}_{k}'
        seen.add(k)
        if not dflt and re.search(r'char\s*\*', t) and 'const' in t: dflt = '""'
        ins.append(dict(id=k, type=t, label=nm or k, default=dflt))
    args = ', '.join('$' + i['id'] for i in ins[1:] if True) if kind == 'm' else ', '.join('$' + i['id'] for i in ins)
    call = e['call']
    if kind == 'c': tpl = call
    elif kind == 'm': tpl = f"$self->{call}({args}{'$,arg' if va else ''})"
    else: tpl = f"{call}({args}{'$,arg' if va else ''})"
    both = kind != 'c' and ret != 'void'
    d = dict(pid=pid, id=eid, plugin=pl, plugin_title=cat['plugin_title'], label=e.get('label') or eid, category=e.get('c') or cat['title'], description=(e.get('d') or '') + ('\n' if e.get('d') else '') + _sig(e),
             flow=kind != 'c', both=both, place='', template=tpl, color=cat['color'], includes=cat['includes'], helpers='', init=[], inputs=ins, output=None if (ret == 'void' or kind == 'c' and not ret) else dict(type=ret if kind != 'c' else (e.get('r') or ''), label='result' if kind != 'c' else 'value'), fields=[])
    if kind == 'c': d['flow'] = False
    if va: d['repeat'] = dict(id='arg', type='', label='argument', min=0, max=8, default=0, field='n_arg'); d['fields'].append(dict(key='n_arg', label='Number of arguments', kind='choice', options=[(str(n), str(n)) for n in range(9)], hint='for the ... of the format', default='0'))
    if d['flow'] and d['output']: d['fields'].append(dict(key='save', label='Save result as', kind='text', options=[], hint='variable name (optional)', default=''))
    _CAT_CACHE[pid] = d; return d


def _sig(e):
    ps = ', '.join(f"{p[0]} {p[1]}" + (f" = {p[2]}" if len(p) > 2 and p[2] else '') for p in (e.get('p') or [])) + (', ...' if e.get('va') else '')
    return f"{e.get('r') or 'void'} {e['call']}({ps})" if e.get('kind', 'f') != 'c' else e['call']
