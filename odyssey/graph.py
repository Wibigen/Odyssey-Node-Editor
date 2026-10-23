"""Graph model, node definitions and exlaunch C++ generation (Qt-independent)."""
import json, re
from collections import namedtuple

from . import plugnodes as PN

E = 'E'  # type of execution pins
Pin = namedtuple('Pin', 'id type label')
Field = namedtuple('Field', 'key label kind opts hint')  # kind: text | type | choice | bool | var | func


def fld(key, label, kind='text', opts=None, hint=''):
    return Field(key, label, kind, opts or [], hint)


DEFAULT_INC = '''#include "Library/LiveActor/LiveActor.h"
#include "Library/LiveActor/ActorMovementFunction.h"
#include "Library/LiveActor/ActorPoseKeeper.h"
#include "Library/Scene/Scene.h"
#include "Scene/StageScene.h"
#include "Player/PlayerActorHakoniwa.h"'''

COMMON_TYPES = ['int', 'float', 'bool', 'const char*', 'u8', 'u32', 's32', 'u64', 'f32', 'void*', 'sead::Vector3f', 'al::LiveActor*']
MODES = [('before', 'Run the original first, then my graph'), ('after', 'Run my graph first, then the original'), ('replace', 'Replace the original (my graph only)'), ('manual', 'Manual: I place "Call original" blocks where I want')]
OPS_MATH = [('+', '+   add'), ('-', '-   subtract'), ('*', '*   multiply'), ('/', '/   divide'), ('%', '%   modulo'), ('&', '&   bitwise and'), ('|', '|   bitwise or'), ('^', '^   bitwise xor'), ('<<', '<<  shift left'), ('>>', '>>  shift right')]
OPS_CMP = [('==', '==  equal'), ('!=', '!=  not equal'), ('<', '<   less than'), ('<=', '<=  less or equal'), ('>', '>   greater than'), ('>=', '>=  greater or equal')]
OPS_LOGIC = [('&&', 'AND  (&&)'), ('||', 'OR  (||)')]
COLOR_NAMES = {'Blue': '#3a7bd5', 'Green': '#2fa66a', 'Orange': '#c98a2b', 'Purple': '#9a66e8', 'Red': '#e8484f', 'Teal': '#14a3a3', 'Pink': '#e0609e', 'Yellow': '#d6c23a', 'Gray': '#7a7f90'}
GROUP_COLORS = list(COLOR_NAMES.values())


def color_name(h):
    return next((k for k, v in COLOR_NAMES.items() if v.lower() == (h or '').lower()), 'Custom')
MARK = re.compile('\x02(\\d+)\x03')
CALLS = ('callgame', 'callfn', 'callmethod', 'callorig', 'callext')
STATIC_CLASS = re.compile(r'(Function|Functions|Util|Utils|Utility|Helper)$')  # classes that only hold static functions (old catalogs do not say)
CALL_STYLES = [('direct', 'Direct call: rs::getPlayerActor(scene)'), ('offset', 'By address: reinterpret_cast<...>(GetTargetOffset(0x...))')]
ARROWS = [('->', 'pointer  ( -> )'), ('.', 'object  ( . )')]
CASTS = [('static_cast', 'static_cast (numbers)'), ('reinterpret_cast', 'reinterpret_cast (pointers)'), ('c', 'C-style cast')]

# palette: label -> (node type, default fields, category, description)
PRE = {
    'Branch (if / else)': ('if', {}, 'Flow', 'Run one path or another depending on a condition.'),
    'Switch': ('switch', {'cases': '0, 1, 2'}, 'Flow', 'Choose a path from an integer value.'),
    'For loop': ('for', {}, 'Flow', 'Repeat a path N times (the index is available as an output).'),
    'While loop': ('while', {}, 'Flow', 'Repeat a path while a condition is true.'),
    'Return': ('ret', {}, 'Flow', 'Leave the current function or hook, optionally with a value.'),
    'Declare variable': ('local', {'type': 'int', 'name': 'myVar'}, 'Variables', 'Create a local variable with an optional initial value.'),
    'Set variable': ('setvar', {'variable': ''}, 'Variables', 'Assign a new value to an existing variable.'),
    'Get variable': ('getvar', {'variable': ''}, 'Variables', 'Read the current value of a variable.'),
    'Global variable': ('global', {'type': 'int', 'name': 'myGlobal', 'init': '0'}, 'Variables', 'A variable that keeps its value between frames and calls.'),
    'Constant (value)': ('literal', {'type': 'float', 'value': '1.0'}, 'Variables', 'A fixed number, text, bool or any C++ value.'),
    'Define function': ('func', {'name': 'myFunction', 'ret': 'void', 'params': 'int a'}, 'Functions', 'Create your own function (entry point of a separate graph).'),
    'Call function': ('callfn', {'name': '', 'save': ''}, 'Functions', 'Call one of your own functions.'),
    'Math (A + B)': ('op', {'op': '+', 'type': 'float'}, 'Math & logic', 'Add, subtract, multiply, divide or modulo two values.'),
    'Compare (A == B)': ('cmp', {'op': '==', 'type': 'float'}, 'Math & logic', 'Compare two values and give a bool.'),
    'Logic (AND / OR)': ('logic', {'op': '&&'}, 'Math & logic', 'Combine two bools.'),
    'NOT': ('not', {}, 'Math & logic', 'Invert a bool.'),
    'Address of (&)': ('addr', {}, 'Pointers & memory', 'Get the address of a value.'),
    'Dereference (*)': ('deref', {}, 'Pointers & memory', 'Read the value a pointer points to.'),
    'Is null?': ('isnull', {'negate': False}, 'Pointers & memory', 'Check whether a pointer is null.'),
    'Cast': ('cast', {'to': 'float', 'how': 'static_cast'}, 'Pointers & memory', 'Convert a value to another type.'),
    'Get member (->)': ('member', {'member': 'field', 'arrow': '->'}, 'Pointers & memory', 'Read a member of an object or pointer.'),
    'Set member (->)': ('setmember', {'member': 'field', 'arrow': '->'}, 'Pointers & memory', 'Write a member of an object or pointer.'),
    'Call original (Orig)': ('callorig', {'save': '', 'inline': False}, 'Functions', 'Inside a hook: call the original game function (with the hook arguments) at this exact point. Use the Manual mode.'),
    'Call method (->)': ('callmethod', {'member': 'method', 'arrow': '->', 'ret': 'void', 'args': '', 'save': '', 'inline': False}, 'Pointers & memory', 'Call a method of an object or pointer, e.g. actor->kill().'),
    'Call by name': ('callext', {'name': 'ns::function', 'ret': 'void', 'args': '', 'save': '', 'inline': False}, 'Functions', 'Call any function by its C++ name (not in the catalog), e.g. sead::Mathf::sqrt(x).'),
    'Construct (new / Type(...))': ('construct', {'type': 'sead::Vector3f', 'new': False, 'args': 'float, float, float'}, 'Pointers & memory', 'Build an object: Type(args), or new Type(args) for a pointer.'),
    'Array element  a[i]': ('index', {}, 'Pointers & memory', 'Read an element of an array (or of any pointer): array[index].'),
    'Set array element  a[i] = v': ('setindex', {}, 'Pointers & memory', 'Write an element of an array (or of any pointer): array[index] = value.'),
    'Get scene object  al::getSceneObj<T>': ('callext', {'name': 'al::getSceneObj', 'targs': 'GameDataHolder', 'ret': '$T*', 'args': 'al::IUseSceneObjHolder const*', 'save': '', 'inline': True}, 'Functions', 'Template call, e.g. al::getSceneObj<GameDataHolder>(stageScene). Change the template type in the inspector.'),
    'Read at offset': ('readoff', {'type': 'float', 'offset': '0x10'}, 'Pointers & memory', 'Read a value at a byte offset from a base pointer.'),
    'Write at offset': ('writeoff', {'type': 'float', 'offset': '0x10'}, 'Pointers & memory', 'Write a value at a byte offset from a base pointer.'),
    'Custom expression': ('expr', {'tpl': '$a', 'type': ''}, 'Custom code', 'Any C++ expression. Inputs: $a ... $h.'),
    'Custom statement': ('stmt', {'tpl': '$a;'}, 'Custom code', 'Any C++ statement. Inputs: $a ... $h.'),
}
CATEGORIES = ['Flow', 'Variables', 'Functions', 'Math & logic', 'Pointers & memory', 'Custom code']
GRP = {c: [k for k, v in PRE.items() if v[2] == c] for c in CATEGORIES}
BUILTIN_PRE, BUILTIN_CATS = dict(PRE), list(CATEGORIES)


def rebuild_palette():
    """Palette entries = built-in blocks + the nodes of the loaded plugins (PRE, CATEGORIES and GRP are updated in place)."""
    PRE.clear(); PRE.update(BUILTIN_PRE); CATEGORIES[:] = BUILTIN_CATS
    for d in sorted(PN.PLUG.values(), key=lambda d: (d['category'].lower(), d['label'].lower())):
        label = d['label'] if d['label'] not in PRE else f"{d['label']} ({d['plugin_title']})"
        PRE[label] = ('plug', PN.defaults(d), d['category'], d['description'])
        if d['category'] not in CATEGORIES: CATEGORIES.insert(len(CATEGORIES) - 1, d['category'])
    GRP.clear(); GRP.update({c: [k for k, v in PRE.items() if v[2] == c] for c in CATEGORIES})


def register_plugin_node(d):
    PN.PLUG[d['pid']] = d


def clear_plugin_nodes():
    PN.EMBED.update(PN.PLUG); PN.PLUG.clear()  # nodes already in a graph keep their definition
KIND_LABEL = dict(hook='Hook: your graph runs when the game calls this function', callgame='Game function call', func='Your function (definition)', callfn='Call of your function', callmethod='Method call', callext='Function call', construct='Object',
                  **{k: 'Flow control' for k in ('if', 'switch', 'for', 'while', 'ret')}, local='Variable', setvar='Variable', getvar='Variable', **{'global': 'Variable'}, literal='Constant',
                  op='Math', cmp='Comparison', logic='Logic', **{'not': 'Logic'}, addr='Pointer', deref='Pointer', isnull='Pointer', cast='Conversion', member='Memory', setmember='Memory',
                  readoff='Memory', writeoff='Memory', index='Memory', setindex='Memory', expr='Custom code', stmt='Custom code')

TYPE_F = fld('type', 'Type', 'type')
INLINE_LABEL = 'Use as a value (no execution pin)'
QUALS = ['', 'static', 'const', 'constexpr', 'static const', 'static constexpr', 'volatile']
ADV_VAR = [fld('qual', 'Qualifier', 'qual', hint='none'), fld('array', 'Array size', hint='empty = a single value, e.g. 8'), fld('ainit', 'Array contents', hint='e.g. 1, 2, 3  (empty = all zero)')]
ADV_KEYS = ('qual', 'array', 'ainit')  # shown in the inspector's collapsed "Advanced" section
NODE_FIELDS = {
    'callorig': [fld('save', 'Save the result in a variable named', hint='optional'), fld('inline', 'Use as a value (no execution pin)', 'bool')],
    'hook': [fld('mode', 'Mode', 'choice', MODES), fld('ret', 'Return type', hint='empty = same as the game function'), fld('names', 'Argument names', hint='empty = p0, p1, ...')],
    'for': [fld('var', 'Index variable', hint='empty = i<id>')],
    'callgame': [fld('via', 'Call style', 'choice', [('', 'Default (Preferences > Advanced)')] + CALL_STYLES), fld('rtype', 'Return type', 'rtype'), fld('inline', INLINE_LABEL, 'bool'), fld('save', 'Save result as', hint='variable name (optional)')],
    'func': [fld('name', 'Name'), fld('ret', 'Return type', 'type'), fld('params', 'Arguments', 'params')],
    'callfn': [fld('name', 'Function', 'func'), fld('inline', INLINE_LABEL, 'bool'), fld('save', 'Save result as', hint='variable name (optional)')],
    'callmethod': [fld('member', 'Method name'), fld('arrow', 'Access through', 'choice', ARROWS), fld('ret', 'Return type', 'type'), fld('args', 'Arguments (types)', 'types'),
                   fld('inline', INLINE_LABEL, 'bool'), fld('save', 'Save result as', hint='variable name (optional)')],
    'callext': [fld('name', 'Function name'), fld('targs', 'Template arguments', hint='e.g. GameDataHolder  for  fn<GameDataHolder>(...)'), fld('ret', 'Return type', 'type', hint='$T = the template argument'), fld('args', 'Arguments (types)', 'types'), fld('inline', INLINE_LABEL, 'bool'), fld('save', 'Save result as', hint='variable name (optional)')],
    'construct': [fld('type', 'Type', 'type'), fld('new', 'Allocate with new (gives a pointer)', 'bool'), fld('args', 'Constructor arguments (types)', 'types')],
    'switch': [fld('cases', 'Cases', 'cases')],
    'local': [TYPE_F, fld('name', 'Name')] + ADV_VAR,
    'global': [TYPE_F, fld('name', 'Name'), fld('init', 'Initial value', hint='0')] + ADV_VAR,
    'setvar': [fld('variable', 'Variable', 'var')], 'getvar': [fld('variable', 'Variable', 'var')],
    'literal': [TYPE_F, fld('value', 'Value')],
    'op': [fld('op', 'Operation', 'choice', OPS_MATH), TYPE_F], 'cmp': [fld('op', 'Comparison', 'choice', OPS_CMP), fld('type', 'Compared type', 'type')],
    'logic': [fld('op', 'Operation', 'choice', OPS_LOGIC)], 'isnull': [fld('negate', 'Invert (is NOT null)', 'bool')],
    'cast': [fld('to', 'Convert to', 'type'), fld('how', 'Cast kind', 'choice', CASTS)],
    'member': [fld('member', 'Member name'), fld('arrow', 'Access through', 'choice', ARROWS)], 'setmember': [fld('member', 'Member name'), fld('arrow', 'Access through', 'choice', ARROWS)],
    'readoff': [TYPE_F, fld('offset', 'Offset (bytes)', hint='0x10')], 'writeoff': [TYPE_F, fld('offset', 'Offset (bytes)', hint='0x10')],
    'expr': [fld('tpl', 'Expression', hint='use $a ... $h for inputs'), fld('type', 'Result type', 'type')], 'stmt': [fld('tpl', 'Statement', hint='use $a ... $h for inputs')],
}
UNKNOWN = dict(n='?', c='', p=[], r='void', o=0, st='N', s='')
IDENT = re.compile(r'^[A-Za-z_]\w*$')


# ---------------- typed values ----------------
def _strip(t): return re.sub(r'\s+', ' ', re.sub(r'\bconst\b|&', '', t or '')).strip()
def is_text_type(t): return bool(re.fullmatch(r'\s*(const\s+)?char\s*(const\s*)?\*\s*', t or ''))
def is_bool(t): return _strip(t) == 'bool'
def is_float(t): return _strip(t) in ('float', 'f32', 'double', 'f64')
def is_int(t): return bool(re.fullmatch(r'(unsigned |signed )?(int|long|short|char|size_t)( long)?|[us](8|16|32|64)|u?int(8|16|32|64)_t', _strip(t)))


def editor_kind(t):
    if is_text_type(t): return 'text'
    if is_bool(t): return 'bool'
    if is_float(t): return 'float'
    if is_int(t): return 'int'
    if 'Vector3' in (t or '') and '*' not in t: return 'vec3'
    return 'raw'


def zero(t):
    """Neutral value for an empty input of this type."""
    t = t or ''
    if '*' in t: return 'nullptr'
    if is_bool(t): return 'false'
    if is_float(t): return '0.0f'
    return '0' if is_int(t) else ('0' if not t else '{}')


def fmt_value(t, raw):
    """C++ text for a fixed value typed in the UI ('' = unset)."""
    raw = ('' if raw is None else str(raw)).strip()
    if not raw: return ''
    if is_text_type(t): return raw if raw.startswith('"') else '"' + raw.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    if is_bool(t): return 'true' if raw.lower() in ('true', '1', 'yes', 'on') else 'false'
    if _strip(t) in ('float', 'f32') and re.fullmatch(r'[-+]?\d+(\.\d*)?([eE][-+]?\d+)?', raw): return raw + ('f' if re.search(r'[.eE]', raw) else '.0f')
    return raw


def split_top(s):
    """Split on commas that are not inside <>, () or []."""
    out, d, cur = [], 0, ''
    for ch in s or '':
        d += (ch in '<([') - (ch in '>)]')
        if ch == ',' and d <= 0: out.append(cur.strip()); cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur.strip())
    return out


def parse_params(s):
    out = []
    for x in split_top(s):
        m = re.match(r'^(.*?)(\w+)$', x)
        out.append((m[2], m[1].strip() or 'int') if m else (x, 'int'))
    return out


def placeholders(tpl):
    return sorted({m[1] for m in re.finditer(r'\$([a-h])', tpl or '')})


def fields_for(n):
    """Inspector fields of a node (plugin nodes bring their own)."""
    if n.type != 'plug': return NODE_FIELDS.get(n.type, [])
    d = PN.plug_def(n.f.get('pid'))
    return [Field(f['key'], f['label'], f['kind'], f['options'], f['hint']) for f in d['fields']] if d else []


def argname(c, i):
    return 'this' if c.get('c') and i == 0 else f'arg {i + 1}'


class Node:
    def __init__(self, id, type, f, x=0.0, y=0.0, d=None):
        self.id, self.type, self.f, self.x, self.y, self.d = id, type, f, x, y, d or {}


class Graph:
    def __init__(self):
        self.nodes, self.edges, self.nid, self.cat, self.inc = {}, [], 1, {}, DEFAULT_INC  # edges: ((id, pin), (id, pin))
        self.groups, self.notes, self.gid, self.overrides, self._mk, self.install, self._qm, self.favorites, self.calls = {}, {}, 1, {}, False, 'symbol', None, [], 'direct'  # groups/notes are visual only

    def set_catalog(self, entries):
        self.cat, self._qm = {}, None
        for e in entries:
            c = dict(e); cls = c.get('c', ''); k = c.get('k') or ''
            if k == 'c': pass  # constructor
            elif not cls: k = 'f'  # free function (namespace)
            else:
                k = k or ('s' if STATIC_CLASS.search(cls) else 'm')  # static or member function of a class
                if k == 's' and c.get('p') and c['p'][0] == cls + '*': c['p'] = c['p'][1:]  # the catalog adds a 'this' parameter to every class function
            c['k'] = k; self.cat[c['s']] = c

    def q(self, t):
        """Qualify class names the catalog printed without their namespace (LiveActor* -> al::LiveActor*), using the qualified spellings seen in the catalog's parameter lists."""
        if not t: return t
        if self._qm is None:
            from collections import Counter
            cnt = {}
            for c in self.cat.values():
                for s in list(c.get('p', [])) + [c.get('r', '')]:
                    for m in re.finditer(r'(?<![\w:])((?:\w+::)+)([A-Z]\w*)', s or ''): cnt.setdefault(m[2], Counter())[m[1] + m[2]] += 1
            self._qm = {k: v.most_common(1)[0][0] for k, v in cnt.items() if len(v) == 1 or v.most_common(1)[0][1] > 3 * sum(v.values()) / 4}
        return re.sub(r'(?<![\w:])([A-Z]\w*)(?![\w:(])', lambda m: self._qm.get(m[1], m[1]), t)

    # ---------------- editing ----------------
    def add(self, type, f, x=0.0, y=0.0, d=None):
        n = Node(self.nid, type, dict(f), x, y, dict(d or {})); self.nodes[n.id] = n; self.nid += 1; return n

    def remove(self, nid):
        self.nodes.pop(nid, None); self.edges = [e for e in self.edges if nid not in (e[0][0], e[1][0])]
        for g in self.groups.values(): g['nodes'] = [i for i in g['nodes'] if i != nid]
        self._gc()

    def duplicate(self, nid):
        n = self.nodes[nid]; return self.add(n.type, n.f, n.x + 30, n.y + 30, n.d)

    def clear(self):
        self.nodes, self.edges, self.nid, self.groups, self.notes, self.gid = {}, [], 1, {}, {}, 1

    # ---------------- groups and comments (visual only) ----------------
    def _gc(self):
        self.groups = {k: v for k, v in self.groups.items() if v['nodes']}

    def add_to_group(self, gid, ids):
        """Put nodes into an existing group (a node belongs to one group at most)."""
        ids = [i for i in ids if i in self.nodes]
        if gid not in self.groups or not ids: return
        for k, v in self.groups.items():
            if k != gid: v['nodes'] = [i for i in v['nodes'] if i not in ids]
        self.groups[gid]['nodes'] += [i for i in ids if i not in self.groups[gid]['nodes']]; self._gc()

    def group_of(self, nid):
        return next((k for k, v in self.groups.items() if nid in v['nodes']), None)

    def make_group(self, ids, name='Group', color=''):
        ids = [i for i in ids if i in self.nodes]
        if not ids: return None
        for v in self.groups.values(): v['nodes'] = [i for i in v['nodes'] if i not in ids]
        self._gc(); gid = self.gid; self.gid += 1
        self.groups[gid] = dict(name=name, color=color or GROUP_COLORS[(gid - 1) % len(GROUP_COLORS)], nodes=list(ids)); return gid

    def add_note(self, text, x, y, color=''):
        nid = self.gid; self.gid += 1; self.notes[nid] = dict(text=text, x=x, y=y, color=color or '#c98a2b'); return nid

    def linked(self, nid, pin, d):
        return any(e[1 if d == 'i' else 0] == (nid, pin) for e in self.edges)

    def pin_type(self, nid, pin, d):
        p = self.find_pin(self.nodes[nid], pin, d); return p.type if p else ''

    def find_pin(self, n, pin, d):
        return next((p for p in self.spec(n)[1 if d == 'i' else 2] if p.id == pin), None)

    def connect(self, a, b):  # a, b = (id, pin, 'i'|'o')
        if a[2] == b[2] or a[0] == b[0] or (self.pin_type(*a) == E) != (self.pin_type(*b) == E): return False
        o, i = (a, b) if a[2] == 'o' else (b, a)
        ex = self.pin_type(*o) == E
        self.edges = [e for e in self.edges if not (e[1] == (i[0], i[1]) and not ex) and not (ex and e[0] == (o[0], o[1]))]
        self.edges.append(((o[0], o[1]), (i[0], i[1]))); return True

    def prune(self):
        """Drop links whose pin no longer exists (after a node was edited)."""
        def ok(nid, pin, d): return nid in self.nodes and self.find_pin(self.nodes[nid], pin, d) is not None
        self.edges = [e for e in self.edges if ok(e[0][0], e[0][1], 'o') and ok(e[1][0], e[1][1], 'i')]

    # ---------------- serialisation ----------------
    def to_json(self):
        return json.dumps({'N': {str(i): dict(id=n.id, type=n.type, f=n.f, d=n.d, x=n.x, y=n.y) for i, n in self.nodes.items()},
                           'EG': [[list(e[0]), list(e[1])] for e in self.edges], 'NID': self.nid, 'inc': self.inc,
                           'GR': {str(k): v for k, v in self.groups.items()}, 'NT': {str(k): v for k, v in self.notes.items()}, 'GID': self.gid,
                           'PD': {p: PN.plug_def(p) for p in sorted({n.f.get('pid') for n in self.nodes.values() if n.type == 'plug'}) if PN.plug_def(p)}})

    def load_json(self, s):
        j = json.loads(s) if isinstance(s, str) else s
        self.nodes = {int(k): Node(int(v['id']), v['type'], v['f'], v.get('x', 0), v.get('y', 0), v.get('d')) for k, v in j['N'].items()}
        self.edges = [((e['f'][0], e['f'][1]), (e['t'][0], e['t'][1])) if isinstance(e, dict) else ((e[0][0], e[0][1]), (e[1][0], e[1][1])) for e in j['EG']]
        for p, d in (j.get('PD') or {}).items():  # definitions saved with the graph: used when the plugin is not installed
            if p not in PN.PLUG and isinstance(d, dict) and 'template' in d and 'fields' in d: PN.EMBED[p] = d
        self.nid = j['NID']; self.inc = j.get('inc') or self.inc
        self.groups = {int(k): dict(v, nodes=[i for i in v.get('nodes', []) if i in self.nodes]) for k, v in (j.get('GR') or {}).items()}; self._gc()
        self.notes = {int(k): v for k, v in (j.get('NT') or {}).items()}; self.gid = max([j.get('GID', 1)] + [k + 1 for k in list(self.groups) + list(self.notes)])
        for n in self.nodes.values():  # fields added since older versions
            for f in fields_for(n): n.f.setdefault(f.key, False if f.kind == 'bool' else '')

    # ---------------- lookups ----------------
    def sg(self, n):
        return self.cat.get(n.f.get('sym'), UNKNOWN)

    def haystack(self, n):
        """everything a node shows or stores that a search can match: title, names, variables, values, expressions, game function."""
        c = self.sg(n) if n.type in ('hook', 'callgame') else None
        bits = [self.title(n), n.type, self.subtitle(n)] + [str(v) for v in n.f.values()] + [str(v) for v in n.d.values()]
        if c is not None and c is not UNKNOWN: bits += [c.get('n', ''), c.get('s', ''), c.get('c', '')]
        try: bits += [p.label for p in self.spec(n)[1] + self.spec(n)[2]]
        except Exception: pass
        return '\n'.join(b for b in bits if b).lower()

    def search_ids(self, q):
        """ids of the nodes that mention q (case-insensitive); every word of q must be found."""
        words = [w for w in q.lower().split() if w]
        if not words: return set()
        return {i for i, n in self.nodes.items() if all(w in self.haystack(n) for w in words)}

    def fn(self, n):
        return next((m for m in self.nodes.values() if m.type == 'func' and m.f.get('name') == n.f.get('name')), None)

    def function_names(self):
        return sorted({n.f['name'] for n in self.nodes.values() if n.type == 'func' and n.f.get('name')})

    def variable_names(self):
        out = set()
        for n in self.nodes.values():
            if n.type in ('local', 'global') and n.f.get('name'): out.add(n.f['name'])
            if (n.type in CALLS or n.type == 'plug') and n.f.get('save'): out.add(n.f['save'])
            if n.type == 'func': out |= {k for k, _ in parse_params(n.f.get('params'))}
        return sorted(out)

    def ret_type(self, n):
        """Return type of a call node: your override, the saved override for this game function, or the catalog guess."""
        T, f = n.type, n.f
        if T == 'callgame': return self.q(f.get('rtype') or self.overrides.get(f.get('sym')) or self.sg(n)['r'])
        if T == 'callfn': m = self.fn(n); return (m.f.get('ret') or 'void') if m else 'void'
        if T == 'callmethod': return self.q(f.get('ret') or 'void')
        if T == 'callext': return self.q((f.get('ret') or 'void').replace('$T', split_top(f.get('targs'))[0] if split_top(f.get('targs')) else 'auto'))
        if T == 'callorig': h = self.hook_of(n.id); return (h.f.get('ret') or self.sg(h)['r']) if h else 'void'
        if T == 'plug': d = PN.plug_def(f.get('pid')); return (d['output']['type'] or 'auto') if d and d['output'] else 'void'
        return 'void'

    def var_type(self, name):
        for n in self.nodes.values():
            if n.type in ('local', 'global') and n.f.get('name') == name: return n.f.get('type', '')
            if n.type == 'func':
                for k, t in parse_params(n.f.get('params')):
                    if k == name: return t
            if (n.type in CALLS or n.type == 'plug') and n.f.get('save') == name: return self.ret_type(n)
        return ''

    def category(self, n):
        if n.type == 'plug':
            d = PN.plug_def(n.f.get('pid')); return d['category'] if d else 'Plugin node'
        return KIND_LABEL.get(n.type, '')

    # ---------------- node description ----------------
    def title(self, n):
        f, T = n.f, n.type
        if T in ('hook', 'callgame'):
            c = self.sg(n); name = c['n'] if f.get('sym') in self.cat else 'Unknown: ' + str(f.get('sym'))
            return ('Hook ' + name) if T == 'hook' else name
        return {'func': lambda: 'Function ' + f.get('name', ''), 'callfn': lambda: 'Call ' + (f.get('name') or '?'), 'callmethod': lambda: f"Call {f.get('arrow', '->')}{f.get('member') or '?'}()", 'callext': lambda: 'Call ' + (f.get('name') or '?') + ('<' + f['targs'] + '>' if f.get('targs') else ''), 'construct': lambda: ('new ' if f.get('new') else '') + (f.get('type') or '?') + '(…)', 'callorig': lambda: 'Call original (Orig)', 'if': lambda: 'Branch (if / else)', 'switch': lambda: 'Switch',
                'for': lambda: 'For loop', 'while': lambda: 'While loop', 'ret': lambda: 'Return', 'local': lambda: f"Declare {f.get('type', '')} {f.get('name', '')}",
                'setvar': lambda: f"Set {f.get('variable') or '?'}", 'getvar': lambda: f"Get {f.get('variable') or '?'}", 'global': lambda: f"Global {f.get('type', '')} {f.get('name', '')}",
                'literal': lambda: f"Constant ({f.get('type', '')})", 'op': lambda: f"A {f.get('op', '+')} B", 'cmp': lambda: f"A {f.get('op', '==')} B",
                'logic': lambda: 'A AND B' if f.get('op', '&&') == '&&' else 'A OR B', 'not': lambda: 'NOT', 'addr': lambda: 'Address of (&)', 'deref': lambda: 'Dereference (*)',
                'isnull': lambda: 'Is NOT null?' if f.get('negate') else 'Is null?', 'cast': lambda: f"Cast to {f.get('to', '')}", 'index': lambda: 'Array element [ ]', 'setindex': lambda: 'Set array element [ ]',
                'member': lambda: f"Get member {f.get('arrow', '->')}{f.get('member', '')}", 'setmember': lambda: f"Set member {f.get('arrow', '->')}{f.get('member', '')}",
                'readoff': lambda: f"Read {f.get('type', '')} at +{f.get('offset', '0')}", 'writeoff': lambda: f"Write {f.get('type', '')} at +{f.get('offset', '0')}",
                'expr': lambda: 'Custom expression', 'stmt': lambda: 'Custom statement', 'plug': lambda: self.plug_title(n)}.get(T, lambda: T)()

    def plug_title(self, n):
        d = PN.plug_def(n.f.get('pid')); return d['label'] if d else 'Missing plugin node ' + str(n.f.get('pid'))

    def subtitle(self, n):
        f, T = n.f, n.type
        if T == 'hook': return dict(MODES).get(f.get('mode'), '')
        if T in ('expr', 'stmt'): return f.get('tpl', '')
        if T in ('local', 'global') and (f.get('qual') or f.get('array')):
            return ' '.join(x for x in [f.get('qual'), f"[{f['array']}]" if f.get('array') else '', ('= ' + str(f['init'])) if T == 'global' and f.get('init') and not f.get('array') else ''] if x)
        if T == 'global' and f.get('init'): return '= ' + str(f['init'])
        if T == 'literal': return str(f.get('value', ''))
        if T == 'plug':
            d = PN.plug_def(f.get('pid')); return d['plugin_title'] if d else 'plugin not found'
        if T == 'func': return 'returns ' + (f.get('ret') or 'void')
        if T in CALLS:
            r = self.ret_type(n); bits = []
            if r != 'void' or T == 'callfn': bits.append('returns ' + r)
            if f.get('inline'): bits.append('inline value')
            return ' · '.join(bits)
        return ''

    def has_inline(self, n):
        """Plugin node that can be used as a value (it returns something and is not a plain statement)."""
        d = PN.plug_def(n.f.get('pid')) if n.type == 'plug' else None
        return bool(d and d['both'])

    def plug_spec(self, n, ei, en):
        d = PN.plug_def(n.f.get('pid'))
        if not d: return [], []
        ins, outs = PN.pins(d, n.f)
        fl = PN.is_flow(d, n.f)
        return ([ei] if fl else []) + [Pin(i, t, l) for i, t, l in ins], ([en] if fl else []) + [Pin(i, t, (f.get('save') or l) if (fl and i == 'out') else l) for (i, t, l), f in ((o, n.f) for o in outs)]

    def plug_text(self, n):
        d = PN.plug_def(n.f.get('pid'))
        def arg(k):
            p = next((i for i in PN.pins(d, n.f)[0] if i[0] == k), None); dflt = next((i['default'] for i in d['inputs'] if i['id'] == k), '')
            return self.val(n, k) or dflt or zero(p[1] if p else '')
        return PN.render(d, n.f, arg)

    def spec(self, n):
        """(title, inputs, outputs); every pin is a Pin(id, type, label); E = execution."""
        f, T = n.f, n.type
        ei, en = Pin('in', E, ''), Pin('next', E, '')
        P = Pin
        if T == 'hook':
            c = self.sg(n); R = f.get('ret') or c['r']
            return self.title(n), [], [en] + [P(f'p{i}', t, argname(c, i)) for i, t in enumerate(c['p'])] + ([P('orig', R, 'original result')] if f.get('mode') == 'before' and R != 'void' else [])
        if T in CALLS:
            if T == 'callgame': c = self.sg(n); ins = [P(f'a{i}', t, argname(c, i)) for i, t in enumerate(c['p'])]
            elif T == 'callfn': m = self.fn(n); ins = [P(k, t, k) for k, t in parse_params(m.f.get('params'))] if m else []
            elif T == 'callorig': ins = []
            elif T == 'callext': ins = [P(f'm{i}', t, f'arg {i + 1}') for i, t in enumerate(split_top(f.get('args')))]
            else: ins = [P('a', 'void*', 'object')] + [P(f'm{i}', t, f'arg {i + 1}') for i, t in enumerate(split_top(f.get('args')))]
            r = self.ret_type(n); outs = [P('ret', r, (f.get('save') or 'result') if not f.get('inline') else 'result')] if r != 'void' else []
            return (self.title(n), ins, outs) if f.get('inline') else (self.title(n), [ei] + ins, [en] + outs)
        if T == 'func': return self.title(n), [], [en] + [P(k, t, k) for k, t in parse_params(f.get('params'))]
        t = f.get('type', '')
        spec = {
            'if': ([ei, P('c', 'bool', 'condition')], [P('then', E, 'True'), P('else', E, 'False'), P('next', E, 'After')]),
            'switch': ([ei, P('v', 'int', 'value')], [P('c:' + x.strip(), E, 'case ' + x.strip()) for x in f.get('cases', '').split(',') if x.strip()] + [P('c:default', E, 'default'), P('next', E, 'After')]),
            'for': ([ei, P('n', 'int', 'count')], [P('body', E, 'Loop body'), P('next', E, 'Completed'), P('i', 'int', 'index')]),
            'while': ([ei, P('c', 'bool', 'condition')], [P('body', E, 'Loop body'), P('next', E, 'Completed')]),
            'ret': ([ei, P('v', '', 'value')], []),
            'local': ([ei, P('v', t, 'initial value')], [en, P('var', t, f.get('name', ''))]),
            'setvar': ([ei, P('v', self.var_type(f.get('variable')), 'new value')], [en]),
            'getvar': ([], [P('out', self.var_type(f.get('variable')), 'value')]),
            'global': ([], [P('var', t, f.get('name', 'value'))]),
            'literal': ([], [P('out', t, 'value')]),
            'op': ([P('a', t, 'A'), P('b', t, 'B')], [P('out', t, 'result')]),
            'cmp': ([P('a', t, 'A'), P('b', t, 'B')], [P('out', 'bool', 'result')]),
            'logic': ([P('a', 'bool', 'A'), P('b', 'bool', 'B')], [P('out', 'bool', 'result')]),
            'not': ([P('a', 'bool', 'value')], [P('out', 'bool', 'result')]),
            'addr': ([P('a', '', 'value')], [P('out', 'void*', 'pointer')]),
            'deref': ([P('a', 'void*', 'pointer')], [P('out', '', 'value')]),
            'isnull': ([P('a', 'void*', 'pointer')], [P('out', 'bool', 'result')]),
            'cast': ([P('a', '', 'value')], [P('out', f.get('to', ''), 'result')]),
            'index': ([P('a', '', 'array'), P('b', 'int', 'index')], [P('out', '', 'element')]),
            'setindex': ([ei, P('a', '', 'array'), P('b', 'int', 'index'), P('c', '', 'value')], [en]),
            'construct': ([P(f'm{i}', t, f'arg {i + 1}') for i, t in enumerate(split_top(f.get('args')))], [P('out', (t + '*') if f.get('new') else t, 'object')]),
            'member': ([P('a', 'void*', 'object')], [P('out', '', f.get('member', 'value'))]),
            'setmember': ([ei, P('a', 'void*', 'object'), P('b', '', 'value')], [en]),
            'readoff': ([P('a', 'void*', 'base pointer')], [P('out', t, 'value')]),
            'writeoff': ([ei, P('a', 'void*', 'base pointer'), P('b', t, 'value')], [en]),
            'plug': self.plug_spec(n, ei, en),
            'expr': ([P(k, '', k.upper()) for k in placeholders(f.get('tpl'))], [P('out', t, 'result')]),
            'stmt': ([ei] + [P(k, '', k.upper()) for k in placeholders(f.get('tpl'))], [en]),
        }.get(T, ([], []))
        return self.title(n), spec[0], spec[1]

    # ---------------- validation ----------------
    def reachable(self):
        seen, st = set(), [n.id for n in self.nodes.values() if n.type in ('hook', 'func')]
        while st:
            i = st.pop()
            if i in seen: continue
            seen.add(i)
            st += [e[1][0] for e in self.edges if e[0][0] == i and self.pin_type(e[0][0], e[0][1], 'o') == E]
        return seen

    def problems(self):
        """List of (level, node id, message); level = 'err' or 'warn'."""
        out, reach, seen_h, names = [], self.reachable(), {}, {}
        declared = set(self.variable_names())
        for n in self.nodes.values():
            T, title = n.type, self.title(n)
            if T in ('hook', 'callgame') and n.f.get('sym') not in self.cat: out.append(('err', n.id, f'{title}: symbol not found in the catalog'))
            if T == 'hook':
                if n.f.get('sym') in seen_h: out.append(('err', n.id, f'{title}: this function is already hooked by another node'))
                seen_h[n.f.get('sym')] = n.id
            if T == 'plug' and not PN.is_loaded(n.f.get('pid')): out.append(('warn', n.id, f"{title}: its plugin is not loaded (the copy saved in the graph is used)"))
            if T in ('func', 'global'):
                k = n.f.get('name')
                if k in names: out.append(('err', n.id, f'Name "{k}" is defined more than once'))
                names[k] = n.id
            for key in ('name', 'save', 'variable'):
                v = n.f.get(key)
                if T in ('func', 'global', 'local', 'setvar', 'getvar') + CALLS and v and not IDENT.match(v): out.append(('err', n.id, f'{title}: "{v}" is not a valid C++ name'))
            if T in ('setvar', 'getvar') and n.f.get('variable') and n.f['variable'] not in declared:
                out.append(('warn', n.id, f'{title}: variable "{n.f["variable"]}" is not declared anywhere'))
            if T == 'callorig':
                h = self.hook_of(n.id)
                if not h: out.append(('err', n.id, f'{title}: only works inside a hook (connect it to a Hook node)'))
                elif h.f.get('mode') == 'replace': out.append(('err', n.id, f'{title}: the hook is in Replace mode, which has no original (use Manual mode)'))
                elif h.f.get('mode') in ('before', 'after'): out.append(('warn', n.id, f'{title}: the hook already calls the original ("{h.f.get("mode")}" mode): use Manual mode to place it yourself'))
            if T == 'callfn' and not self.fn(n): out.append(('err', n.id, f'Call to "{n.f.get("name") or "?"}": function not defined'))
            inline = T in CALLS and n.f.get('inline')
            pd = PN.plug_def(n.f.get('pid')) if T == 'plug' else None
            if inline and self.ret_type(n) == 'void': out.append(('err', n.id, f'{title}: returns void, so it cannot be used as a value'))
            if T == 'local' and n.id not in reach: out.append(('info', n.id, f'{title}: not inside any function, so it is declared as a global variable')); continue
            if (T in CALLS and not inline) or T in ('if', 'switch', 'for', 'while', 'local', 'setvar', 'setmember', 'setindex', 'writeoff', 'stmt', 'ret') or (pd and PN.is_flow(pd, n.f)):
                if n.id not in reach: out.append(('warn', n.id, f'{title}: unreachable (not connected to a Hook or Function)')); continue
            if T in ('local', 'ret', 'hook', 'func', 'global') or (pd and pd['place']): continue
            if (inline or T in ('expr', 'literal', 'op', 'cmp', 'logic', 'not', 'addr', 'deref', 'isnull', 'cast', 'member', 'readoff', 'getvar', 'construct', 'index') or (pd and not PN.is_flow(pd, n.f) and not pd['place'])) and not any(e[0][0] == n.id for e in self.edges): continue
            for p in self.spec(n)[1]:
                if pd and (any(i['id'] == p.id and i['default'] for i in pd['inputs']) or (pd.get('repeat') and p.id.startswith(pd['repeat']['id']))): continue  # the plugin gives a default
                if p.type != E and not self.linked(n.id, p.id, 'i') and not str(n.d.get(p.id, '')).strip(): out.append(('warn', n.id, f'{title}: input "{p.label}" is empty (a default value is used)'))
        return out

    # ---------------- C++ generation ----------------
    def nxt(self, nid, pin):
        return next((e[1][0] for e in self.edges if e[0] == (nid, pin)), None)

    def val(self, n, pin):
        e = next((e for e in self.edges if e[1] == (n.id, pin)), None)
        return self.ex(self.nodes[e[0][0]], e[0][1]) if e else fmt_value(self.pin_type(n.id, pin, 'i'), n.d.get(pin, ''))

    def arg(self, n, pin):
        return self.val(n, pin) or zero(self.pin_type(n.id, pin, 'i'))

    def _m(self, nid):
        return f'\x02{nid}\x03' if self._mk else ''

    def ex(self, n, p):
        r = self._ex(n, p)
        return self._m(n.id) + r if r else r

    def hook_of(self, nid):
        """The hook node whose flow contains this node (walking the execution links backwards), or None."""
        seen, st = set(), [nid]
        while st:
            i = st.pop()
            if i in seen: continue
            seen.add(i); node = self.nodes.get(i)
            if node and node.type == 'hook': return node
            st += [e[0][0] for e in self.edges if e[1][0] == i and e[1][1] == 'in']  # 'in' is the execution input of every node (no spec() here: it would recurse)
        return None

    def call_text(self, n):
        """The call itself, as a C++ expression."""
        f, T = n.f, n.type
        if T == 'callgame':
            c = self.sg(n); args = [self.arg(n, f'a{i}') for i in range(len(c['p']))]; a = ', '.join(args); via = f.get('via') or self.calls
            if via == 'direct' and c is not UNKNOWN and re.fullmatch(r'[A-Za-z_]\w*(::[A-Za-z_]\w*)*', c.get('n', '?')) and c.get('k') != 'c':  # only plain C++ names can be called directly (not thunks, operators, sub_XXXX)  # the plain call: the decomp headers declare the function, the base links the symbol
                if c.get('k') == 'm' and args:
                    obj = args[0] if re.fullmatch(r'\w+', args[0]) else f'({args[0]})'; return f"{obj}->{c['n'].rsplit('::', 1)[-1]}({', '.join(args[1:])})"
                return f"{c['n']}({a})"
            rt = self.ret_type(n); rt = 'void*' if rt == 'auto' else rt  # 'auto' only works with a direct call
            return f"reinterpret_cast<{rt}(*)({', '.join(c['p'])})>(exl::util::modules::GetTargetOffset(0x{c['o']:x}))({a})"
        if T == 'callorig':
            h = self.hook_of(n.id); return f"Orig({', '.join(self.hook_names(h))})" if h else 'Orig()'
        if T == 'callfn':
            m = self.fn(n); return f"{f.get('name', '')}({', '.join(self.arg(n, k) for k, _ in parse_params(m.f.get('params')))})" if m else ''
        if T == 'callext': return f"{f.get('name', '')}{'<' + f['targs'] + '>' if f.get('targs') else ''}({', '.join(self.arg(n, f'm{i}') for i in range(len(split_top(f.get('args')))))})"
        return f"{self.arg(n, 'a')}{f.get('arrow', '->')}{f.get('member', '')}({', '.join(self.arg(n, f'm{i}') for i in range(len(split_top(f.get('args')))))})"

    def decl(self, f, init):
        """[qualifier] Type name[size] [= init]  (a variable declaration, without the final ';')"""
        q, arr = (f.get('qual') or '').strip(), str(f.get('array') or '').strip()
        s = (q + ' ' if q else '') + f"{self.q(f.get('type', ''))} {f.get('name', '')}"
        if arr: s += arr if arr.startswith('[') else f'[{arr}]'; ai = str(f.get('ainit') or '').strip(); return s + ' = {' + ai + '}'
        return s + (' = ' + init if init else '')

    def hook_names(self, n):
        given = split_top(n.f.get('names'))
        return [given[i] if i < len(given) and IDENT.match(given[i]) else f'p{i}' for i in range(len(self.sg(n)['p']))]

    def _ex(self, n, p):
        f, T = n.f, n.type
        if T == 'hook': return 'orig_ret' if p == 'orig' else (self.hook_names(n)[int(p[1:])] if re.fullmatch(r'p\d+', p) and int(p[1:]) < len(self.sg(n)['p']) else p)
        if T == 'func': return p
        if T in ('local', 'global'): return f.get('name', '')
        if T == 'for': return f.get('var') or f'i{n.id}'
        if T in CALLS: return self.call_text(n) if f.get('inline') else (f.get('save') or f'r{n.id}')
        if T == 'getvar': return f.get('variable', '')
        if T == 'plug':
            d = PN.plug_def(f.get('pid'))
            if not d: return ''
            return (f.get('save') or f'r{n.id}') if PN.is_flow(d, f) else '(' + self.plug_text(n) + ')'
        if T == 'literal': return fmt_value(f.get('type'), f.get('value')) or zero(f.get('type'))
        A, B = self.arg(n, 'a'), self.arg(n, 'b')
        if T in ('op', 'cmp', 'logic'): return f"({A} {f.get('op', '+')} {B})"
        if T == 'not': return f'(!{A})'
        if T == 'addr': return f'(&{A})'
        if T == 'deref': return f'(*{A})'
        if T == 'isnull': return f"({A} {'!=' if f.get('negate') else '=='} nullptr)"
        if T == 'cast':
            to, how = f.get('to', ''), f.get('how', 'static_cast')
            return f'(({to}){A})' if how == 'c' else f'{how}<{to}>({A})'
        if T == 'construct': return ('new ' if f.get('new') else '') + f"{f.get('type', '')}({', '.join(self.arg(n, f'm{i}') for i in range(len(split_top(f.get('args')))))})"
        if T == 'index': return f'{A}[{B}]'
        if T == 'member': return f"({A}{f.get('arrow', '->')}{f.get('member', '')})"
        if T == 'readoff': return f"(*reinterpret_cast<{f.get('type', '')}*>(reinterpret_cast<u8*>({A}) + {f.get('offset') or '0'}))"
        if T == 'expr': return '(' + re.sub(r'\$([a-h])', lambda m: self.arg(n, m[1]), f.get('tpl', '')) + ')'
        return ''

    def chain(self, nid, L):
        o, g, P = '', 0, '  ' * L
        while nid and g < 999:
            g += 1; n = self.nodes[nid]; f, T, cur, s0 = n.f, n.type, nid, len(o)
            b = lambda p, l=L + 1: self.chain(self.nxt(cur, p), l)
            if T in CALLS:
                r, call = self.ret_type(n), self.call_text(n)
                if call: o += f"{P}{call};\n" if r == 'void' else f"{P}{'auto' if T == 'callfn' else r} {self.ex(n, 'ret')} = {call};\n"
            elif T == 'if':
                o += f"{P}if ({self.arg(n, 'c')}) {{\n{b('then')}{P}}}" + (f" else {{\n{b('else')}{P}}}" if self.nxt(nid, 'else') else '') + '\n'
            elif T == 'switch':
                o += f"{P}switch ({self.arg(n, 'v')}) {{\n"
                for p in self.spec(n)[2]:
                    if p.id.startswith('c:'):
                        v = p.id[2:]; o += f"{P}  {'default' if v == 'default' else 'case ' + v}: {{\n{b(p.id, L + 2)}{P}    break;\n{P}  }}\n"
                o += f"{P}}}\n"
            elif T == 'for': v = f.get('var') or f'i{nid}'; o += f"{P}for (int {v} = 0; {v} < {self.arg(n, 'n')}; {v}++) {{\n{b('body')}{P}}}\n"
            elif T == 'while': o += f"{P}while ({self.arg(n, 'c')}) {{\n{b('body')}{P}}}\n"
            elif T == 'local': o += f"{P}{self.decl(f, self.arg(n, 'v'))};\n"
            elif T == 'setvar': o += f"{P}{f.get('variable', '')} = {self.arg(n, 'v')};\n"
            elif T == 'setindex': o += f"{P}{self.arg(n, 'a')}[{self.arg(n, 'b')}] = {self.arg(n, 'c')};\n"
            elif T == 'setmember': o += f"{P}{self.arg(n, 'a')}{f.get('arrow', '->')}{f.get('member', '')} = {self.arg(n, 'b')};\n"
            elif T == 'writeoff': o += f"{P}*reinterpret_cast<{f.get('type', '')}*>(reinterpret_cast<u8*>({self.arg(n, 'a')}) + {f.get('offset') or '0'}) = {self.arg(n, 'b')};\n"
            elif T == 'plug' and PN.plug_def(f.get('pid')) and PN.is_flow(PN.plug_def(f.get('pid')), f):
                d = PN.plug_def(f.get('pid')); s = self.plug_text(n).strip()
                if d['output'] and (f.get('save') or self.linked(n.id, 'out', 'o')): o += f"{P}{d['output']['type'] or 'auto'} {self.ex(n, 'out')} = {s};\n"
                else: o += f"{P}{s}{'' if s[-1:] in (';', '}') else ';'}\n"
            elif T == 'stmt':
                s = re.sub(r'\$([a-h])', lambda m: self.arg(n, m[1]), f.get('tpl', '')).strip()
                o += f"{P}{s}{'' if s[-1:] in (';', '}') else ';'}\n"
            elif T == 'ret':
                v = self.val(n, 'v'); o += f"{P}return{' ' + v if v else ''};\n"
            if self._mk and len(o) > s0: o = o[:s0 + len(P)] + self._m(cur) + o[s0 + len(P):]  # remember which line belongs to which node
            nid = self.nxt(nid, 'next')
        return o

    def plug_defs(self):
        seen, out = set(), []
        for n in self.nodes.values():
            d = PN.plug_def(n.f.get('pid')) if n.type == 'plug' else None
            if d and d['pid'] not in seen: seen.add(d['pid']); out.append(d)
        return out

    def plug_init(self):
        """Code a plugin asks to run once at startup (inside exl_main): the "init" lines of the nodes in use, then every "main" node."""
        o = ''; seen = set()
        for d in self.plug_defs():
            for l in d['init']:
                if l not in seen: seen.add(l); o += f'  {l.strip()}\n'
        for n in sorted((n for n in self.nodes.values() if n.type == 'plug'), key=lambda n: (n.y, n.x, n.id)):
            d = PN.plug_def(n.f.get('pid'))
            if d and d['place'] == 'main':
                s = self.plug_text(n).strip(); o += f"  {self._m(n.id)}{s}{'' if s[-1:] in (';', '}') else ';'}\n"
        return o

    def plug_header(self):
        """#include lines and helper code asked for by the plugin nodes in use."""
        inc = [l for d in self.plug_defs() for l in PN.include_lines(d)]; have = set(self.inc.splitlines()); o = ''
        for l in dict.fromkeys(inc):
            if l not in have: o += l + '\n'
        for d in self.plug_defs():
            if d['helpers'].strip(): o += f"\n// helper from plugin {d['plugin_title']}\n{d['helpers'].strip()}\n"
        return o

    def gen(self):
        V = list(self.nodes.values()); ty = lambda t: [n for n in V if n.type == t]
        o = f'// Generated by Odyssey Node Editor - place in your exlaunch project (src/program/main.cpp)\n#include <exlaunch.hpp>\n{self.inc}\n'
        o += self.plug_header() + '\n'
        for n in ty('global'): o += f"{self._m(n.id)}{self.decl(n.f, n.f.get('init') or '')};\n"
        reach = self.reachable()
        for n in ty('local'):  # a variable declared outside any function is a global
            if n.id not in reach: o += f"{self._m(n.id)}{self.decl(n.f, self.arg(n, 'v'))};\n"
        fs = ty('func')
        for n in fs: o += f"{n.f.get('ret') or 'void'} {n.f.get('name', '')}({n.f.get('params', '')});\n"
        for n in fs: o += f"\n{self._m(n.id)}{n.f.get('ret') or 'void'} {n.f.get('name', '')}({n.f.get('params', '')}) {{\n{self.chain(self.nxt(n.id, 'next'), 1)}}}\n"
        hs = ty('hook')
        for n in hs:
            c = self.sg(n); R = n.f.get('ret') or c['r']; nm = self.hook_names(n); a = ', '.join(nm); m = n.f.get('mode'); v = R != 'void'
            o += f"\n{self._m(n.id)}{'HOOK_DEFINE_REPLACE' if m == 'replace' else 'HOOK_DEFINE_TRAMPOLINE'}(Hook{n.id}) {{\n  static {R} Callback({', '.join(f'{t} {nm[i]}' for i, t in enumerate(c['p']))}) {{\n"
            if m == 'before': o += f"    {R + ' orig_ret = ' if v else ''}Orig({a});\n"
            o += self.chain(self.nxt(n.id, 'next'), 2)
            if m == 'before' and v: o += '    return orig_ret;\n'
            if m == 'after': o += f"    {'return ' if v else ''}Orig({a});\n"
            if m == 'replace' and v: o += '    return {};\n'
            o += '  }\n};\n'
        installs = ''.join(f"  Hook{n.id}::InstallAtSymbol(\"{n.f.get('sym', '')}\");\n" if self.install == 'symbol' and n.f.get('sym') and not str(n.f['sym']).startswith('sub_') else f"  Hook{n.id}::InstallAtOffset(0x{self.sg(n)['o']:x});\n" for n in hs)
        return o + f'\nextern "C" void exl_main(void*, void*) {{\n  exl::hook::Initialize();\n{self.plug_init()}{installs}}}\n\nextern "C" NORETURN void exl_exception_entry() {{ EXL_ABORT(\"Unhandled exception\"); }}\n'

    def gen_map(self):
        """(code, {node id: [0-based line numbers]}) - lets the editor highlight the code of the selected node."""
        self._mk = True
        try: raw = self.gen()
        finally: self._mk = False
        mp, out = {}, []
        for i, ln in enumerate(raw.split('\n')):
            for m in MARK.finditer(ln): mp.setdefault(int(m[1]), set()).add(i)
            out.append(MARK.sub('', ln))
        return '\n'.join(out), {k: sorted(v) for k, v in mp.items()}


def sample(g):
    """Example: frame counter in StageScene::exePlay, using the new nodes."""
    A = g.add
    h = A('hook', {'sym': '_ZN10StageScene7exePlayEv', 'mode': 'before', 'ret': ''}, 20, 20)
    sv = A('setvar', {'variable': 'frames'}, 330, 20); br = A('if', {}, 640, 20); st = A('stmt', {'tpl': '/* TODO: call a game function here */'}, 950, 20)
    gv1 = A('getvar', {'variable': 'frames'}, 20, 190); op1 = A('op', {'op': '+', 'type': 'int'}, 330, 190, {'b': '1'})
    gv2 = A('getvar', {'variable': 'frames'}, 20, 340); op2 = A('op', {'op': '%', 'type': 'int'}, 330, 340, {'b': '60'}); cm = A('cmp', {'op': '==', 'type': 'int'}, 640, 340, {'b': '0'})
    A('global', {'type': 'int', 'name': 'frames', 'init': '0'}, 20, 500)
    g.make_group([gv2.id, op2.id, cm.id], 'Is it the 60th frame?'); g.add_note('Counts frames, then does something once per second (60 frames).', 20, -70)
    g.edges += [((h.id, 'next'), (sv.id, 'in')), ((sv.id, 'next'), (br.id, 'in')), ((br.id, 'then'), (st.id, 'in')), ((gv1.id, 'out'), (op1.id, 'a')), ((op1.id, 'out'), (sv.id, 'v')),
                ((gv2.id, 'out'), (op2.id, 'a')), ((op2.id, 'out'), (cm.id, 'a')), ((cm.id, 'out'), (br.id, 'c'))]
