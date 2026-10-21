"""Graph model, node definitions and exlaunch C++ generation (Qt-independent)."""
import json, re
from collections import namedtuple

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
MODES = [('before', 'Run the original first, then my graph'), ('after', 'Run my graph first, then the original'), ('replace', 'Replace the original (my graph only)')]
OPS_MATH = [('+', '+   add'), ('-', '-   subtract'), ('*', '*   multiply'), ('/', '/   divide'), ('%', '%   modulo')]
OPS_CMP = [('==', '==  equal'), ('!=', '!=  not equal'), ('<', '<   less than'), ('<=', '<=  less or equal'), ('>', '>   greater than'), ('>=', '>=  greater or equal')]
OPS_LOGIC = [('&&', 'AND  (&&)'), ('||', 'OR  (||)')]
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
    'Read at offset': ('readoff', {'type': 'float', 'offset': '0x10'}, 'Pointers & memory', 'Read a value at a byte offset from a base pointer.'),
    'Write at offset': ('writeoff', {'type': 'float', 'offset': '0x10'}, 'Pointers & memory', 'Write a value at a byte offset from a base pointer.'),
    'Custom expression': ('expr', {'tpl': '$a', 'type': ''}, 'Custom code', 'Any C++ expression. Inputs: $a, $b, $c, $d.'),
    'Custom statement': ('stmt', {'tpl': '$a;'}, 'Custom code', 'Any C++ statement. Inputs: $a, $b, $c, $d.'),
}
CATEGORIES = ['Flow', 'Variables', 'Functions', 'Math & logic', 'Pointers & memory', 'Custom code']
GRP = {c: [k for k, v in PRE.items() if v[2] == c] for c in CATEGORIES}
KIND_LABEL = dict(hook='Hook: your graph runs when the game calls this function', callgame='Game function call', func='Your function (definition)', callfn='Call of your function',
                  **{k: 'Flow control' for k in ('if', 'switch', 'for', 'while', 'ret')}, local='Variable', setvar='Variable', getvar='Variable', **{'global': 'Variable'}, literal='Constant',
                  op='Math', cmp='Comparison', logic='Logic', **{'not': 'Logic'}, addr='Pointer', deref='Pointer', isnull='Pointer', cast='Conversion', member='Memory', setmember='Memory',
                  readoff='Memory', writeoff='Memory', expr='Custom code', stmt='Custom code')

TYPE_F = fld('type', 'Type', 'type')
NODE_FIELDS = {
    'hook': [fld('mode', 'Mode', 'choice', MODES), fld('ret', 'Return type', hint='empty = same as the game function')],
    'callgame': [fld('save', 'Save result as', hint='variable name (optional)')],
    'func': [fld('name', 'Name'), fld('ret', 'Return type'), fld('params', 'Parameters', hint='int a, float b')],
    'callfn': [fld('name', 'Function', 'func'), fld('save', 'Save result as', hint='variable name (optional)')],
    'switch': [fld('cases', 'Cases', hint='0, 1, 2')],
    'local': [TYPE_F, fld('name', 'Name')],
    'global': [TYPE_F, fld('name', 'Name'), fld('init', 'Initial value', hint='0')],
    'setvar': [fld('variable', 'Variable', 'var')], 'getvar': [fld('variable', 'Variable', 'var')],
    'literal': [TYPE_F, fld('value', 'Value')],
    'op': [fld('op', 'Operation', 'choice', OPS_MATH), TYPE_F], 'cmp': [fld('op', 'Comparison', 'choice', OPS_CMP), fld('type', 'Compared type', 'type')],
    'logic': [fld('op', 'Operation', 'choice', OPS_LOGIC)], 'isnull': [fld('negate', 'Invert (is NOT null)', 'bool')],
    'cast': [fld('to', 'Convert to', 'type'), fld('how', 'Cast kind', 'choice', CASTS)],
    'member': [fld('member', 'Member name'), fld('arrow', 'Access through', 'choice', ARROWS)], 'setmember': [fld('member', 'Member name'), fld('arrow', 'Access through', 'choice', ARROWS)],
    'readoff': [TYPE_F, fld('offset', 'Offset (bytes)', hint='0x10')], 'writeoff': [TYPE_F, fld('offset', 'Offset (bytes)', hint='0x10')],
    'expr': [fld('tpl', 'Expression', hint='use $a, $b, $c, $d for inputs'), fld('type', 'Result type', 'type')], 'stmt': [fld('tpl', 'Statement', hint='use $a, $b, $c, $d for inputs')],
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


def parse_params(s):
    out = []
    for x in [p.strip() for p in (s or '').split(',') if p.strip()]:
        m = re.match(r'^(.*?)(\w+)$', x)
        out.append((m[2], m[1].strip() or 'int') if m else (x, 'int'))
    return out


def placeholders(tpl):
    return sorted({m[1] for m in re.finditer(r'\$([a-d])', tpl or '')})


def argname(c, i):
    return 'this' if c.get('c') and i == 0 else f'arg {i + 1}'


class Node:
    def __init__(self, id, type, f, x=0.0, y=0.0, d=None):
        self.id, self.type, self.f, self.x, self.y, self.d = id, type, f, x, y, d or {}


class Graph:
    def __init__(self):
        self.nodes, self.edges, self.nid, self.cat, self.inc = {}, [], 1, {}, DEFAULT_INC  # edges: ((id, pin), (id, pin))

    def set_catalog(self, entries):
        self.cat = {c['s']: c for c in entries}

    # ---------------- editing ----------------
    def add(self, type, f, x=0.0, y=0.0, d=None):
        n = Node(self.nid, type, dict(f), x, y, dict(d or {})); self.nodes[n.id] = n; self.nid += 1; return n

    def remove(self, nid):
        self.nodes.pop(nid, None); self.edges = [e for e in self.edges if nid not in (e[0][0], e[1][0])]

    def duplicate(self, nid):
        n = self.nodes[nid]; return self.add(n.type, n.f, n.x + 30, n.y + 30, n.d)

    def clear(self):
        self.nodes, self.edges, self.nid = {}, [], 1

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
                           'EG': [[list(e[0]), list(e[1])] for e in self.edges], 'NID': self.nid, 'inc': self.inc})

    def load_json(self, s):
        j = json.loads(s) if isinstance(s, str) else s
        self.nodes = {int(k): Node(int(v['id']), v['type'], v['f'], v.get('x', 0), v.get('y', 0), v.get('d')) for k, v in j['N'].items()}
        self.edges = [((e['f'][0], e['f'][1]), (e['t'][0], e['t'][1])) if isinstance(e, dict) else ((e[0][0], e[0][1]), (e[1][0], e[1][1])) for e in j['EG']]
        self.nid = j['NID']; self.inc = j.get('inc') or self.inc
        for n in self.nodes.values():  # fields added since older versions
            for f in NODE_FIELDS.get(n.type, []): n.f.setdefault(f.key, False if f.kind == 'bool' else '')

    # ---------------- lookups ----------------
    def sg(self, n):
        return self.cat.get(n.f.get('sym'), UNKNOWN)

    def fn(self, n):
        return next((m for m in self.nodes.values() if m.type == 'func' and m.f.get('name') == n.f.get('name')), None)

    def function_names(self):
        return sorted({n.f['name'] for n in self.nodes.values() if n.type == 'func' and n.f.get('name')})

    def variable_names(self):
        out = set()
        for n in self.nodes.values():
            if n.type in ('local', 'global') and n.f.get('name'): out.add(n.f['name'])
            if n.type in ('callgame', 'callfn') and n.f.get('save'): out.add(n.f['save'])
            if n.type == 'func': out |= {k for k, _ in parse_params(n.f.get('params'))}
        return sorted(out)

    def var_type(self, name):
        for n in self.nodes.values():
            if n.type in ('local', 'global') and n.f.get('name') == name: return n.f.get('type', '')
            if n.type == 'func':
                for k, t in parse_params(n.f.get('params')):
                    if k == name: return t
            if n.type == 'callgame' and n.f.get('save') == name: return self.sg(n)['r']
            if n.type == 'callfn' and n.f.get('save') == name:
                m = self.fn(n); return m.f.get('ret', '') if m else ''
        return ''

    def category(self, n):
        return KIND_LABEL.get(n.type, '')

    # ---------------- node description ----------------
    def title(self, n):
        f, T = n.f, n.type
        if T in ('hook', 'callgame'):
            c = self.sg(n); name = c['n'] if f.get('sym') in self.cat else 'Unknown: ' + str(f.get('sym'))
            return ('Hook ' + name) if T == 'hook' else name
        return {'func': lambda: 'Function ' + f.get('name', ''), 'callfn': lambda: 'Call ' + (f.get('name') or '?'), 'if': lambda: 'Branch (if / else)', 'switch': lambda: 'Switch',
                'for': lambda: 'For loop', 'while': lambda: 'While loop', 'ret': lambda: 'Return', 'local': lambda: f"Declare {f.get('type', '')} {f.get('name', '')}",
                'setvar': lambda: f"Set {f.get('variable') or '?'}", 'getvar': lambda: f"Get {f.get('variable') or '?'}", 'global': lambda: f"Global {f.get('type', '')} {f.get('name', '')}",
                'literal': lambda: f"Constant ({f.get('type', '')})", 'op': lambda: f"A {f.get('op', '+')} B", 'cmp': lambda: f"A {f.get('op', '==')} B",
                'logic': lambda: 'A AND B' if f.get('op', '&&') == '&&' else 'A OR B', 'not': lambda: 'NOT', 'addr': lambda: 'Address of (&)', 'deref': lambda: 'Dereference (*)',
                'isnull': lambda: 'Is NOT null?' if f.get('negate') else 'Is null?', 'cast': lambda: f"Cast to {f.get('to', '')}",
                'member': lambda: f"Get member {f.get('arrow', '->')}{f.get('member', '')}", 'setmember': lambda: f"Set member {f.get('arrow', '->')}{f.get('member', '')}",
                'readoff': lambda: f"Read {f.get('type', '')} at +{f.get('offset', '0')}", 'writeoff': lambda: f"Write {f.get('type', '')} at +{f.get('offset', '0')}",
                'expr': lambda: 'Custom expression', 'stmt': lambda: 'Custom statement'}.get(T, lambda: T)()

    def subtitle(self, n):
        f, T = n.f, n.type
        if T == 'hook': return dict(MODES).get(f.get('mode'), '')
        if T in ('expr', 'stmt'): return f.get('tpl', '')
        if T == 'global' and f.get('init'): return '= ' + str(f['init'])
        if T == 'literal': return str(f.get('value', ''))
        if T in ('callgame', 'callfn') and f.get('save'): return 'result saved as ' + f['save']
        return ''

    def spec(self, n):
        """(title, inputs, outputs); every pin is a Pin(id, type, label); E = execution."""
        f, T = n.f, n.type
        ei, en = Pin('in', E, ''), Pin('next', E, '')
        P = Pin
        if T == 'hook':
            c = self.sg(n); R = f.get('ret') or c['r']
            return self.title(n), [], [en] + [P(f'p{i}', t, argname(c, i)) for i, t in enumerate(c['p'])] + ([P('orig', R, 'original result')] if f.get('mode') == 'before' and R != 'void' else [])
        if T == 'callgame':
            c = self.sg(n)
            return self.title(n), [ei] + [P(f'a{i}', t, argname(c, i)) for i, t in enumerate(c['p'])], [en] + ([P('ret', c['r'], 'result')] if c['r'] != 'void' else [])
        if T == 'func': return self.title(n), [], [en] + [P(k, t, k) for k, t in parse_params(f.get('params'))]
        if T == 'callfn':
            m = self.fn(n); ps = parse_params(m.f.get('params')) if m else []
            return self.title(n), [ei] + [P(k, t, k) for k, t in ps], [en] + ([P('ret', m.f.get('ret', ''), 'result')] if m and m.f.get('ret', 'void') != 'void' else [])
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
            'global': ([], []),
            'literal': ([], [P('out', t, 'value')]),
            'op': ([P('a', t, 'A'), P('b', t, 'B')], [P('out', t, 'result')]),
            'cmp': ([P('a', t, 'A'), P('b', t, 'B')], [P('out', 'bool', 'result')]),
            'logic': ([P('a', 'bool', 'A'), P('b', 'bool', 'B')], [P('out', 'bool', 'result')]),
            'not': ([P('a', 'bool', 'value')], [P('out', 'bool', 'result')]),
            'addr': ([P('a', '', 'value')], [P('out', 'void*', 'pointer')]),
            'deref': ([P('a', 'void*', 'pointer')], [P('out', '', 'value')]),
            'isnull': ([P('a', 'void*', 'pointer')], [P('out', 'bool', 'result')]),
            'cast': ([P('a', '', 'value')], [P('out', f.get('to', ''), 'result')]),
            'member': ([P('a', 'void*', 'object')], [P('out', '', f.get('member', 'value'))]),
            'setmember': ([ei, P('a', 'void*', 'object'), P('b', '', 'value')], [en]),
            'readoff': ([P('a', 'void*', 'base pointer')], [P('out', t, 'value')]),
            'writeoff': ([ei, P('a', 'void*', 'base pointer'), P('b', t, 'value')], [en]),
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
            if T in ('func', 'global'):
                k = n.f.get('name')
                if k in names: out.append(('err', n.id, f'Name "{k}" is defined more than once'))
                names[k] = n.id
            for key in ('name', 'save', 'variable'):
                v = n.f.get(key)
                if T in ('func', 'global', 'local', 'callgame', 'callfn', 'setvar', 'getvar') and v and not IDENT.match(v): out.append(('err', n.id, f'{title}: "{v}" is not a valid C++ name'))
            if T in ('setvar', 'getvar') and n.f.get('variable') and n.f['variable'] not in declared:
                out.append(('warn', n.id, f'{title}: variable "{n.f["variable"]}" is not declared anywhere'))
            if T == 'callfn' and not self.fn(n): out.append(('err', n.id, f'Call to "{n.f.get("name") or "?"}": function not defined'))
            if T in ('callgame', 'callfn', 'if', 'switch', 'for', 'while', 'local', 'setvar', 'setmember', 'writeoff', 'stmt', 'ret'):
                if n.id not in reach: out.append(('warn', n.id, f'{title}: unreachable (not connected to a Hook or Function)')); continue
            if T in ('local', 'ret', 'hook', 'func', 'global'): continue
            if T in ('expr', 'literal', 'op', 'cmp', 'logic', 'not', 'addr', 'deref', 'isnull', 'cast', 'member', 'readoff', 'getvar') and not any(e[0][0] == n.id for e in self.edges): continue
            for p in self.spec(n)[1]:
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

    def ex(self, n, p):
        f, T = n.f, n.type
        if T == 'hook': return 'orig_ret' if p == 'orig' else p
        if T == 'func': return p
        if T == 'local': return f.get('name', '')
        if T == 'for': return f'i{n.id}'
        if T in ('callgame', 'callfn'): return f.get('save') or f'r{n.id}'
        if T == 'getvar': return f.get('variable', '')
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
        if T == 'member': return f"({A}{f.get('arrow', '->')}{f.get('member', '')})"
        if T == 'readoff': return f"(*reinterpret_cast<{f.get('type', '')}*>(reinterpret_cast<u8*>({A}) + {f.get('offset') or '0'}))"
        if T == 'expr': return '(' + re.sub(r'\$([a-d])', lambda m: self.arg(n, m[1]), f.get('tpl', '')) + ')'
        return ''

    def chain(self, nid, L):
        o, g, P = '', 0, '  ' * L
        while nid and g < 999:
            g += 1; n = self.nodes[nid]; f, T, cur = n.f, n.type, nid
            b = lambda p, l=L + 1: self.chain(self.nxt(cur, p), l)
            if T == 'callgame':
                c = self.sg(n); a = ', '.join(self.arg(n, f'a{i}') for i in range(len(c['p']))); r = c['r']
                o += f"{P}{r + ' ' + self.ex(n, 'ret') + ' = ' if r != 'void' else ''}reinterpret_cast<{r}(*)({', '.join(c['p'])})>(exl::util::modules::GetTargetOffset(0x{c['o']:x}))({a});\n"
            elif T == 'callfn':
                m = self.fn(n)
                if m: o += f"{P}{'auto ' + self.ex(n, 'ret') + ' = ' if m.f.get('ret', 'void') != 'void' else ''}{f['name']}({', '.join(self.arg(n, k) for k, _ in parse_params(m.f.get('params')))});\n"
            elif T == 'if':
                o += f"{P}if ({self.arg(n, 'c')}) {{\n{b('then')}{P}}}" + (f" else {{\n{b('else')}{P}}}" if self.nxt(nid, 'else') else '') + '\n'
            elif T == 'switch':
                o += f"{P}switch ({self.arg(n, 'v')}) {{\n"
                for p in self.spec(n)[2]:
                    if p.id.startswith('c:'):
                        v = p.id[2:]; o += f"{P}  {'default' if v == 'default' else 'case ' + v}: {{\n{b(p.id, L + 2)}{P}    break;\n{P}  }}\n"
                o += f"{P}}}\n"
            elif T == 'for': o += f"{P}for (int i{nid} = 0; i{nid} < {self.arg(n, 'n')}; i{nid}++) {{\n{b('body')}{P}}}\n"
            elif T == 'while': o += f"{P}while ({self.arg(n, 'c')}) {{\n{b('body')}{P}}}\n"
            elif T == 'local': o += f"{P}{f.get('type', '')} {f.get('name', '')} = {self.arg(n, 'v')};\n"
            elif T == 'setvar': o += f"{P}{f.get('variable', '')} = {self.arg(n, 'v')};\n"
            elif T == 'setmember': o += f"{P}{self.arg(n, 'a')}{f.get('arrow', '->')}{f.get('member', '')} = {self.arg(n, 'b')};\n"
            elif T == 'writeoff': o += f"{P}*reinterpret_cast<{f.get('type', '')}*>(reinterpret_cast<u8*>({self.arg(n, 'a')}) + {f.get('offset') or '0'}) = {self.arg(n, 'b')};\n"
            elif T == 'stmt':
                s = re.sub(r'\$([a-d])', lambda m: self.arg(n, m[1]), f.get('tpl', '')).strip()
                o += f"{P}{s}{'' if s[-1:] in (';', '}') else ';'}\n"
            elif T == 'ret':
                v = self.val(n, 'v'); o += f"{P}return{' ' + v if v else ''};\n"
            nid = self.nxt(nid, 'next')
        return o

    def gen(self):
        V = list(self.nodes.values()); ty = lambda t: [n for n in V if n.type == t]
        o = f'// Generated by Odyssey Nodes - place in your exlaunch project (src/program/main.cpp)\n#include "lib.hpp"\n{self.inc}\n\n'
        for n in ty('global'): o += f"{n.f.get('type', '')} {n.f.get('name', '')}{' = ' + n.f['init'] if n.f.get('init') else ''};\n"
        fs = ty('func')
        for n in fs: o += f"{n.f.get('ret', 'void')} {n.f.get('name', '')}({n.f.get('params', '')});\n"
        for n in fs: o += f"\n{n.f.get('ret', 'void')} {n.f.get('name', '')}({n.f.get('params', '')}) {{\n{self.chain(self.nxt(n.id, 'next'), 1)}}}\n"
        hs = ty('hook')
        for n in hs:
            c = self.sg(n); R = n.f.get('ret') or c['r']; a = ', '.join(f'p{i}' for i in range(len(c['p']))); m = n.f.get('mode'); v = R != 'void'
            o += f"\nHOOK_DEFINE_TRAMPOLINE(Hook{n.id}) {{\n  static {R} Callback({', '.join(f'{t} p{i}' for i, t in enumerate(c['p']))}) {{\n"
            if m == 'before': o += f"    {R + ' orig_ret = ' if v else ''}Orig({a});\n"
            o += self.chain(self.nxt(n.id, 'next'), 2)
            if m == 'before' and v: o += '    return orig_ret;\n'
            if m == 'after': o += f"    {'return ' if v else ''}Orig({a});\n"
            if m == 'replace' and v: o += '    return {};\n'
            o += '  }\n};\n'
        installs = ''.join(f"  Hook{n.id}::InstallAtOffset(0x{self.sg(n)['o']:x});\n" for n in hs)
        return o + f'\nextern "C" void exl_main(void*, void*) {{\n  exl::hook::Initialize();\n{installs}}}\n\nextern "C" NORETURN void exl_exception_entry() {{ EXL_ABORT(0x420); }}\n'


def sample(g):
    """Example: frame counter in StageScene::exePlay, using the new nodes."""
    A = g.add
    h = A('hook', {'sym': '_ZN10StageScene7exePlayEv', 'mode': 'before', 'ret': ''}, 20, 20)
    sv = A('setvar', {'variable': 'frames'}, 330, 20); br = A('if', {}, 640, 20); st = A('stmt', {'tpl': '/* TODO: call a game function here */'}, 950, 20)
    gv1 = A('getvar', {'variable': 'frames'}, 20, 190); op1 = A('op', {'op': '+', 'type': 'int'}, 330, 190, {'b': '1'})
    gv2 = A('getvar', {'variable': 'frames'}, 20, 340); op2 = A('op', {'op': '%', 'type': 'int'}, 330, 340, {'b': '60'}); cm = A('cmp', {'op': '==', 'type': 'int'}, 640, 340, {'b': '0'})
    A('global', {'type': 'int', 'name': 'frames', 'init': '0'}, 20, 500)
    g.edges += [((h.id, 'next'), (sv.id, 'in')), ((sv.id, 'next'), (br.id, 'in')), ((br.id, 'then'), (st.id, 'in')), ((gv1.id, 'out'), (op1.id, 'a')), ((op1.id, 'out'), (sv.id, 'v')),
                ((gv2.id, 'out'), (op2.id, 'a')), ((op2.id, 'out'), (cm.id, 'a')), ((cm.id, 'out'), (br.id, 'c'))]
