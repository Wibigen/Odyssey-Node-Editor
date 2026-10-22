"""Best-effort conversion of C++ (exlaunch mod code) into a node graph. Anything it cannot understand becomes a
"Custom statement" / "Custom expression" node holding the original text, so the generated code stays equivalent."""
import re

from .graph import Graph, parse_params
from .layout import apply as arrange

TOK = re.compile(r'''(?P<ws>\s+)|(?P<lc>//[^\n]*)|(?P<bc>/\*.*?\*/)|(?P<str>"(?:\\.|[^"\\])*")|(?P<chr>'(?:\\.|[^'\\])*')
  |(?P<num>0[xX][0-9a-fA-F]+[uUlL]*|\d+\.?\d*(?:[eE][-+]?\d+)?[fFuUlL]*|\.\d+[fF]?)|(?P<id>[A-Za-z_]\w*)
  |(?P<op>->|::|==|!=|<=|>=|&&|\|\||<<=|>>=|\+\+|--|\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|>>|[^\s\w])''', re.X | re.S)
PRIM = {'int', 'float', 'bool', 'double', 'char', 'short', 'long', 'unsigned', 'signed', 'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64', 'size_t', 'uintptr_t', 'void'}
QUAL = {'static', 'inline', 'extern', 'NORETURN', 'constexpr', 'volatile'}
BIN = {'||': 4, '&&': 5, '|': 6, '^': 7, '&': 8, '==': 9, '!=': 9, '<': 10, '<=': 10, '>': 10, '>=': 10, '<<': 11, '>>': 11, '+': 12, '-': 12, '*': 13, '/': 13, '%': 13}
ASSIGN = {'=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^='}
OPEN, CLOSE = ('(', '[', '{'), (')', ']', '}')


class ParseError(Exception): pass


class Tok:
    __slots__ = ('k', 'x', 's', 'e')
    def __init__(self, k, x, s, e): self.k, self.x, self.s, self.e = k, x, s, e


EOF = Tok('eof', '', 0, 0)


def tokenize(src):
    out = []
    for m in TOK.finditer(src):
        if m.lastgroup not in ('ws', 'lc', 'bc'): out.append(Tok(m.lastgroup, m.group(), m.start(), m.end()))
    return out


class Parser:
    def __init__(self, src):
        self.src, self.t, self.i, self.lim = src, tokenize(src), 0, 0
        self.lim = len(self.t)

    # ---- token helpers ----
    def peek(self, k=0): return self.t[self.i + k] if self.i + k < min(self.lim, len(self.t)) else EOF
    def at(self, x, k=0): return self.peek(k).x == x
    def take(self): t = self.peek(); self.i += 1; return t
    def accept(self, x):
        if self.at(x): self.i += 1; return True
        return False
    def expect(self, x):
        if not self.accept(x): raise ParseError(f'expected {x}')
    def raw(self, a, b): return self.src[self.t[a].s:self.t[b - 1].e] if b > a else ''

    def match(self, i):
        """index of the token closing the bracket opened at i"""
        d = 0
        for j in range(i, len(self.t)):
            x = self.t[j].x
            if x in OPEN: d += 1
            elif x in CLOSE:
                d -= 1
                if d == 0: return j
        raise ParseError('unbalanced brackets')

    def stmt_end(self, i, lim):
        """index of the ';' ending the statement that starts at i (top-level, brackets skipped)"""
        j = i
        while j < lim:
            x = self.t[j].x
            if x in OPEN: j = self.match(j)
            elif x == ';': return j
            j += 1
        return lim

    # ---- expressions ----
    def expr(self, minp=3):
        s = self.i; left = self.unary()
        while self.i < self.lim:
            x = self.peek().x
            if x == '?' and minp <= 3:
                self.i += 1; a = self.expr(); self.expect(':'); b = self.expr(3); left = ('tern', s, self.i, left, a, b); continue
            p = BIN.get(x)
            if p is None or p < minp: break
            self.i += 1; right = self.expr(p + 1); left = ('bin', s, self.i, x, left, right)
        return left

    def type_until(self, close):
        """tokens of a type up to the matching close angle bracket (the opening '<' is already consumed)"""
        s, d = self.i, 1
        while self.i < self.lim:
            x = self.peek().x
            d += x.count('<') - x.count('>') if x in ('<', '>', '>>') else 0
            if d <= 0: break
            self.i += 1
        if d > 0: raise ParseError('bad template')
        e = self.i; self.i += 1; return self.raw(s, e)

    def tmpl_end(self, i):
        """index of the '>' closing the template argument list that opens at token i, when it is really one (types only, followed by '(')"""
        d = 0
        for q in range(i, min(self.lim, len(self.t))):
            x = self.t[q].x
            if x == '<': d += 1
            elif x in ('>', '>>'):
                d -= len(x)
                if d <= 0: return q if d == 0 and q + 1 < self.lim and self.t[q + 1].x == '(' else None
            elif not (self.t[q].k in ('id', 'num') or x in ('::', '*', '&', ',')): return None
        return None

    def typelike(self, a, b):
        return b > a and all(self.t[k].k == 'id' or self.t[k].x in ('::', '*', '&', '<', '>', '>>', ',') for k in range(a, b))

    def unary(self):
        s, t = self.i, self.peek()
        if t.x == '!': self.i += 1; return ('not', s, self.i, self.unary())
        if t.x == '-':
            self.i += 1
            if self.peek().k == 'num' and self.peek().s == t.e: n = self.take(); return ('num', s, self.i, '-' + n.x)
            return ('neg', s, self.i, self.unary())
        if t.x == '*': self.i += 1; return ('deref', s, self.i, self.unary())
        if t.x == '&': self.i += 1; return ('addr', s, self.i, self.unary())
        if t.x in ('~', '++', '--', '+'): self.i += 1; return ('pre', s, self.i, t.x, self.unary())
        if t.x == 'new' and self.peek(1).k == 'id':
            self.i += 1; a = self.i
            while self.i < self.lim and not self.at('(') and not self.at(';'): self.i += 1
            ty = self.raw(a, self.i); args = []
            if self.accept('('):
                while not self.at(')'):
                    args.append(self.expr())
                    if not self.accept(','): break
                self.expect(')')
            return ('new', s, self.i, ty.strip(), args)
        if t.x in ('static_cast', 'reinterpret_cast', 'const_cast') and self.at('<', 1):
            self.i += 2; ty = self.type_until('>'); self.expect('('); e = self.expr(); self.expect(')'); return self.postfix(('cast', s, self.i, t.x, ty, e), s)
        if t.x == '(':
            j = self.match(self.i)
            inner = self.typelike(self.i + 1, j) and (any(self.t[k].x == '*' for k in range(self.i + 1, j)) or self.t[self.i + 1].x in PRIM or self.t[self.i + 1].x == 'const')
            nxt = self.t[j + 1] if j + 1 < self.lim else EOF
            if inner and (nxt.k in ('id', 'num', 'str') or nxt.x in ('(', '-', '*', '&', '!')):
                ty = self.raw(self.i + 1, j); self.i = j + 1; return ('ccast', s, self.i, ty, self.unary())
            self.i += 1; e = self.expr(); self.expect(')'); return self.postfix(e, s)
        return self.postfix(self.primary(), s)

    def primary(self):
        s, t = self.i, self.take()
        if t.k == 'num': return ('num', s, self.i, t.x)
        if t.k in ('str', 'chr'): return ('str', s, self.i, t.x)
        if t.k == 'id':
            if t.x in ('true', 'false', 'nullptr'): return ('lit', s, self.i, t.x)
            name = t.x
            while self.at('::') and self.peek(1).k == 'id': self.i += 1; name += '::' + self.take().x
            if self.at('<') and self.tmpl_end(self.i) is not None: self.i += 1; name += '<' + self.type_until('>').strip() + '>'  # al::getSceneObj<GameDataHolder>(...)
            return ('id', s, self.i, name)
        raise ParseError('unexpected ' + t.x)

    def postfix(self, e, s):
        while self.i < self.lim:
            x = self.peek().x
            if x in ('->', '.') and self.peek(1).k == 'id': self.i += 2; e = ('member', s, self.i, x, e, self.t[self.i - 1].x)
            elif x == '(':
                self.i += 1; args = []
                while not self.at(')'):
                    args.append(self.expr()); 
                    if not self.accept(','): break
                self.expect(')'); e = ('call', s, self.i, e, args)
            elif x == '[': self.i += 1; ix = self.expr(); self.expect(']'); e = ('index', s, self.i, e, ix)
            elif x in ('++', '--'): self.i += 1; e = ('post', s, self.i, x, e)
            else: break
        return e

    def arglist(self, a, b):
        """comma separated expressions in the token range [a, b)"""
        out, d, s = [], 0, a
        for q in range(a, b + 1):
            x = self.t[q].x if q < b else ','
            if x in OPEN: d += 1
            elif x in CLOSE: d -= 1
            elif x == ',' and d == 0:
                if q > s: out.append(self.parse_expr(s, q))
                s = q + 1
        return out

    def parse_expr(self, a, b):
        """whole token range [a, b) as one expression, or ParseError"""
        keep = (self.i, self.lim); self.i, self.lim = a, b
        try:
            e = self.expr()
            if self.i != b: raise ParseError('trailing tokens')
            return e
        finally: self.i, self.lim = keep

    # ---- statements ----
    def block(self, a, b):
        keep = (self.i, self.lim); self.i, self.lim = a, b; out = []
        try:
            while self.i < self.lim: out += self.stmt()
        finally: self.i, self.lim = keep
        return out

    def skip_stmt(self):
        t = self.peek()
        if t.x == '{': self.i = self.match(self.i) + 1
        elif t.x in ('if', 'for', 'while', 'switch'):
            self.i += 1
            if self.at('('): self.i = self.match(self.i) + 1
            self.skip_stmt()
            if t.x == 'if' and self.at('else'): self.i += 1; self.skip_stmt()
        else: self.i = min(self.stmt_end(self.i, self.lim) + 1, self.lim)

    def body(self):
        """the statement after if/for/while (a block or one statement) as a list"""
        return self.stmt()

    def stmt(self):
        a, t = self.i, self.peek()
        if t.x == ';': self.i += 1; return []
        if t.x == '{': j = self.match(self.i); a0 = self.i + 1; self.i = j + 1; return self.block(a0, j)
        try:
            if t.x == 'if': return [self.s_if()]
            if t.x == 'for': return [self.s_for()]
            if t.x == 'while': return [self.s_while()]
            if t.x == 'switch': return [self.s_switch()]
        except ParseError:
            self.i = a; self.skip_stmt(); return [('raw', self.raw(a, self.i))]
        j = self.stmt_end(self.i, self.lim); self.i = min(j + 1, self.lim)
        return self.simple(a, j) if j > a else []

    def paren(self):
        self.expect('('); j = self.match(self.i - 1); a = self.i; self.i = j + 1; return a, j

    def s_if(self):
        self.expect('if'); a, j = self.paren(); c = self.parse_expr(a, j); then = self.body(); els = None
        if self.accept('else'): els = self.body()
        return ('if', c, then, els)

    def s_while(self):
        self.expect('while'); a, j = self.paren(); return ('while', self.parse_expr(a, j), self.body())

    def s_for(self):
        self.expect('for'); a, j = self.paren(); h = self.raw(a, j)
        m = re.fullmatch(r'\s*(?:int|u32|s32|u64|s64|size_t|auto)\s+(\w+)\s*=\s*0\s*;\s*\1\s*<\s*(.+?)\s*;\s*(?:\1\s*\+\+|\+\+\s*\1)\s*', h, re.S)
        if not m: raise ParseError('for')
        sub = Parser(m[2]); n = sub.parse_expr(0, len(sub.t))
        return ('for', m[1], (sub, n), self.body())

    def s_switch(self):
        self.expect('switch'); a, j = self.paren(); v = self.parse_expr(a, j)
        if not self.at('{'): raise ParseError('switch')
        end = self.match(self.i); self.i += 1; cases, cur = [], None
        while self.i < end:
            if self.at('case') or self.at('default'):
                label = 'default' if self.take().x == 'default' else None
                if label is None:
                    s = self.i
                    while not self.at(':') and self.i < self.lim: self.i += 1
                    label = self.raw(s, self.i)
                self.expect(':'); cur = [label, []]; cases.append(cur)
            elif cur is None: raise ParseError('switch')
            else: cur[1] += self.stmt()
        self.i = end + 1
        for k, (lab, body) in enumerate(cases):
            if body and body[-1][0] == 'raw' and body[-1][1].strip() == 'break;': body.pop()
            elif k < len(cases) - 1: raise ParseError('fallthrough')
        return ('switch', v, cases)

    def simple(self, a, j):
        t0 = self.t[a].x
        if t0 == 'return':
            return [('ret', self.parse_expr(a + 1, j) if j > a + 1 else None, self.raw(a, j) + ';')]
        if t0 in ('break', 'continue', 'goto', 'delete', 'throw', 'do'): return [('raw', self.raw(a, j) + ';')]
        if j - a >= 2 and self.t[j - 1].x in ('++', '--') and self.t[a].x not in ('++', '--'):  # counter++ / counter--
            try: return [('assign', self.parse_expr(a, j - 1), self.t[j - 1].x[0] + '=', ('num', j - 1, j, '1'))]
            except ParseError: return [('raw', self.raw(a, j) + ';')]
        if j - a >= 2 and self.t[a].x in ('++', '--'):  # ++counter / --counter
            try: return [('assign', self.parse_expr(a + 1, j), self.t[a].x[0] + '=', ('num', a, a + 1, '1'))]
            except ParseError: return [('raw', self.raw(a, j) + ';')]
        k, d = None, 0
        for q in range(a, j):
            x = self.t[q].x
            if x in OPEN: d += 1
            elif x in CLOSE: d -= 1
            elif d == 0 and x in ASSIGN: k = q; break
        try:
            qb = next((q for q in range(a, j) if self.t[q].x == '['), None)  # Type name[size] [= {…}];
            if qb is not None and (k is None or qb < k) and qb - a >= 2 and self.t[qb - 1].k == 'id' and self.t[qb - 2].x != '::' and self.typelike(a, qb - 1):
                m = self.match(qb)
                if m == j - 1: return [('adecl', self.raw(a, qb - 1), self.t[qb - 1].x, self.raw(qb + 1, m), '')]
                if self.t[m + 1].x == '=' and self.t[m + 2].x == '{' and self.match(m + 2) == j - 1: return [('adecl', self.raw(a, qb - 1), self.t[qb - 1].x, self.raw(qb + 1, m), self.raw(m + 3, j - 1))]
                return [('raw', self.raw(a, j) + ';')]
            if k is None:  # Type name(args);   (constructor-style declaration)
                po = next((q for q in range(a, j) if self.t[q].x == '('), None)
                if po is not None and po - a >= 2 and self.t[po - 1].k == 'id' and self.t[po - 2].x != '::' and self.typelike(a, po - 1) and self.match(po) == j - 1 and self.t[a].x not in ('return', 'new', 'delete'):
                    return [('decl', self.raw(a, po - 1), self.t[po - 1].x, ('brace', po, j, None, self.arglist(po + 1, j - 1)))]
                if not any(self.t[q].x == '(' for q in range(a, j)) and j - a >= 2 and self.typelike(a, j) and self.t[j - 1].k == 'id' and self.t[j - 2].x != '::':
                    return [('decl', self.raw(a, j - 1), self.t[j - 1].x, None)]
                e = self.parse_expr(a, j)
                return [('call', e)] if e[0] == 'call' else [('raw', self.raw(a, j) + ';')]
            lhs_decl = k - a >= 2 and self.typelike(a, k) and self.t[k - 1].k == 'id' and self.t[k - 2].x != '::' and self.t[k].x == '='
            if lhs_decl and self.t[k + 1].x == '{' and self.match(k + 1) == j - 1:  # Type name = {a, b, c};
                return [('decl', self.raw(a, k - 1), self.t[k - 1].x, ('brace', k + 1, j, None, self.arglist(k + 2, j - 1)))]
            rhs = self.parse_expr(k + 1, j)
            if lhs_decl: return [('decl', self.raw(a, k - 1), self.t[k - 1].x, rhs)]
            lhs = self.parse_expr(a, k)
            return [('assign', lhs, self.t[k].x, rhs)]
        except ParseError: return [('raw', self.raw(a, j) + ';')]


# =====================================================================
def sym_by_offset(graph):
    d = {}
    for c in graph.cat.values(): d.setdefault(c['o'], c)
    return d


class Importer:
    def __init__(self, graph):
        self.g, self.report, self.offs = graph, [], sym_by_offset(graph)
        self.scope, self.types, self.funcs, self.ids = {}, {}, {}, []
        self.byname, self.bymethod, self.bysuffix, self.hook_ret, self.hook_args = {}, {}, {}, 'void', []
        for e in graph.cat.values():
            if e.get('k') != 'c': self.byname.setdefault(e['n'], []).append(e)
            if e.get('k') == 'm': self.bymethod.setdefault(e['n'].rsplit('::', 1)[-1], []).append(e)
            elif e.get('k') != 'c':
                parts = e['n'].split('::')
                for i in range(len(parts)): self.bysuffix.setdefault('::'.join(parts[i:]), []).append(e)  # 'isHidePane' and 'al::isHidePane' both find al::isHidePane

    # ---- node helpers ----
    def node(self, type_, f, d=None):
        n = self.g.add(type_, f, 0, 0, d); self.ids.append(n.id); return n

    def link(self, a, ap, b, bp): self.g.edges.append(((a, ap), (b, bp)))

    def feed(self, ast, nid, pin):
        r = self.expr(ast)
        if r[0] == 'fix': self.g.nodes[nid].d[pin] = r[1]
        else: self.link(r[1], r[2], nid, pin)

    def raw_expr(self, p, ast):
        return ('wire', self.node('expr', {'tpl': p.raw(ast[1], ast[2]), 'type': ''}).id, 'out')

    def guess(self, p, a):
        k = a[0]
        if k == 'num': return 'float' if re.search(r'[.eE]|[fF]$', a[3]) and not a[3].lower().startswith('0x') else 'int'
        if k == 'id': return self.types.get(a[3], '')
        if k == 'bin': return self.guess(p, a[4]) or self.guess(p, a[5])
        return ''

    # ---- expressions ----
    def expr(self, ast, p=None):
        p = p or self.p; k = ast[0]
        if k in ('num', 'str'): return ('fix', ast[3])
        if k == 'lit': return ('fix', ast[3])
        if k == 'id':
            name = ast[3]
            if name in self.scope: return ('wire', *self.scope[name])
            if name in self.types: return ('wire', self.node('getvar', {'variable': name}).id, 'out')
            return self.raw_expr(p, ast)
        if k == 'bin':
            op, a, b = ast[3], ast[4], ast[5]
            if op in ('==', '!=') and b[0] == 'lit' and b[3] == 'nullptr':
                n = self.node('isnull', {'negate': op == '!='}); self.feed(a, n.id, 'a'); return ('wire', n.id, 'out')
            if op in ('+', '-', '*', '/', '%', '&', '|', '^', '<<', '>>'): n = self.node('op', {'op': op, 'type': self.guess(p, ast) or 'int'})
            elif op in ('==', '!=', '<', '<=', '>', '>='): n = self.node('cmp', {'op': op, 'type': self.guess(p, ast) or 'int'})
            elif op in ('&&', '||'): n = self.node('logic', {'op': op})
            else: n = self.node('expr', {'tpl': f'($a {op} $b)', 'type': ''})
            self.feed(a, n.id, 'a'); self.feed(b, n.id, 'b'); return ('wire', n.id, 'out')
        if k == 'not': n = self.node('not', {}); self.feed(ast[3], n.id, 'a'); return ('wire', n.id, 'out')
        if k == 'addr': n = self.node('addr', {}); self.feed(ast[3], n.id, 'a'); return ('wire', n.id, 'out')
        if k == 'deref':
            off = self.offset_pattern(p, ast[3])
            if off:
                n = self.node('readoff', {'type': off[0], 'offset': off[1]}); self.feed(off[2], n.id, 'a'); return ('wire', n.id, 'out')
            n = self.node('deref', {}); self.feed(ast[3], n.id, 'a'); return ('wire', n.id, 'out')
        if k == 'cast':
            if ast[3] != 'const_cast': n = self.node('cast', {'to': ast[4], 'how': ast[3]}); self.feed(ast[5], n.id, 'a'); return ('wire', n.id, 'out')
        if k == 'ccast': n = self.node('cast', {'to': ast[3], 'how': 'c'}); self.feed(ast[4], n.id, 'a'); return ('wire', n.id, 'out')
        if k == 'member' and ast[5] not in ('Orig',):
            n = self.node('member', {'member': ast[5], 'arrow': ast[3]}); self.feed(ast[4], n.id, 'a'); return ('wire', n.id, 'out')
        if k in ('new', 'brace'):
            n = self.node('construct', {'type': ast[3], 'new': k == 'new', 'args': ', '.join(self.guess(p, a) or 'auto' for a in ast[4])})
            for i, a in enumerate(ast[4]): self.feed(a, n.id, f'm{i}')
            return ('wire', n.id, 'out')
        if k == 'call':
            c = self.call_node(p, ast, inline=True)
            if c: return ('wire', c.id, 'ret')
        if k == 'index':
            n = self.node('index', {}); self.feed(ast[3], n.id, 'a'); self.feed(ast[4], n.id, 'b'); return ('wire', n.id, 'out')
        if k in ('neg', 'tern', 'post', 'pre'):
            parts = {'neg': ('(-$a)', [ast[3]]), 'tern': ('($a ? $b : $c)', [ast[3], ast[4], ast[5]]),
                     'post': (f'$a{ast[3]}', [ast[4]]), 'pre': (f'({ast[3]}$a)', [ast[4]])}[k]
            n = self.node('expr', {'tpl': parts[0], 'type': ''})
            for q, sub in zip('abc', parts[1]): self.feed(sub, n.id, q)
            return ('wire', n.id, 'out')
        return self.raw_expr(p, ast)

    def offset_pattern(self, p, a):
        """*reinterpret_cast<T*>(reinterpret_cast<u8*>(base) + offset)  ->  (T, offset, base)"""
        if a[0] == 'cast' and a[3] == 'reinterpret_cast' and a[4].strip().endswith('*') and a[5][0] == 'bin' and a[5][3] == '+':
            l = a[5][4]
            if l[0] == 'cast' and l[4].replace(' ', '') == 'u8*': return a[4].strip()[:-1].strip(), p.raw(a[5][5][1], a[5][5][2]), l[5]
        return None

    def call_node(self, p, ast, inline, save='', declared=''):
        """a call expression -> callgame / callfn / callmethod node (None if not recognised)"""
        callee, args = ast[3], ast[4]
        f = {'inline': inline, 'save': save}
        mt = re.fullmatch(r'(.+?)<(.*)>', callee[3], re.S) if callee[0] == 'id' else None
        if mt:  # a template function: al::getSceneObj<GameDataHolder>(scene)
            base = mt[1]; rt = declared if declared and declared != 'auto' else ('$T*' if base.rsplit('::', 1)[-1] in ('getSceneObj', 'tryGetSceneObj') else 'auto')
            n = self.node('callext', {'name': base, 'targs': mt[2].strip(), 'ret': rt if (save or inline) else 'void', 'args': ', '.join(self.guess(p, a) or 'auto' for a in args), **f})
            for i, a in enumerate(args): self.feed(a, n.id, f'm{i}')
            return n
        if callee[0] == 'cast' and callee[3] == 'reinterpret_cast' and callee[5][0] == 'call' and callee[5][3][0] == 'id' and callee[5][3][3].endswith('GetTargetOffset') and callee[5][4] and callee[5][4][0][0] == 'num':
            c = self.offs.get(int(callee[5][4][0][3].rstrip('uUlL'), 0))
            if not c: self.report.append(f'No catalog function at offset {callee[5][4][0][3]}: kept as custom code'); return None
            m = re.match(r'\s*(.+?)\s*\(\*\)', callee[4]); rt = m[1] if m else ''
            n = self.node('callgame', {'sym': c['s'], 'save': save, 'inline': inline, 'rtype': rt if rt and rt != c['r'] else ''})
            for i, a in enumerate(args[:len(c['p'])]): self.feed(a, n.id, f'a{i}')
            return n
        if callee[0] == 'id' and callee[3] == 'Orig':  # the original function inside a hook (arguments are the hook's own)
            n = self.node('callorig', f)
            if [p.raw(a[1], a[2]).strip() for a in args] != self.hook_args: self.report.append(f'Orig({", ".join(p.raw(a[1], a[2]) for a in args)}) uses other arguments than the hook\'s: the hook arguments are used')
            return n
        if callee[0] == 'id' and callee[3] in self.funcs:
            fn = self.funcs[callee[3]]; n = self.node('callfn', {'name': callee[3], **f})
            for (k, _), a in zip(parse_params(fn.f.get('params')), args): self.feed(a, n.id, k)
            return n
        if callee[0] == 'id' and callee[3] in self.byname:  # rs::getPlayerActor(scene), GameDataFunction::isGotShine(...): a direct call of a game function
            cs = [e for e in self.byname[callee[3]] if len(e['p']) == len(args)]
            if cs: return self.game_call(p, cs[0], args, f, declared, 0)
        if callee[0] == 'id' and callee[3] in self.bysuffix:  # isHidePane(layout, "Bg0") without its namespace: found by the end of the name
            cs = [e for e in self.bysuffix[callee[3]] if len(e['p']) == len(args)]
            if len({e['n'] for e in cs}) > 1:
                pri = [e for e in cs if e['n'].split('::')[0] in ('al', 'rs')]
                if len({e['n'] for e in pri}) == 1: cs = pri
            if cs and len({e['n'] for e in cs}) == 1: return self.game_call(p, cs[0], args, f, declared, 0)
            if cs: self.report.append(f'{callee[3]}: several catalog functions match ({", ".join(sorted({e["n"] for e in cs})[:3])}...); kept as a call by name')
        if callee[0] == 'member' and callee[5] != 'Orig':
            cs = [e for e in self.bymethod.get(callee[5], []) if len(e['p']) == len(args) + 1]  # obj->method(args): a member of a catalog class, when the name is not ambiguous
            if cs and len({e['n'] for e in cs}) == 1:
                n = self.game_call(p, cs[0], [callee[4]] + list(args), f, declared, 0); return n
            n = self.node('callmethod', {'member': callee[5], 'arrow': callee[3], 'ret': (declared or 'auto') if (save or inline) else 'void', 'args': ', '.join('auto' for _ in args), **f})
            self.feed(callee[4], n.id, 'a')
            for i, a in enumerate(args): self.feed(a, n.id, f'm{i}')
            return n
        if callee[0] == 'id' and callee[3] not in ('Orig',):  # any other function or constructor, by its name
            last = callee[3].rsplit('::', 1)[-1]
            if last[:1].isupper() and (inline or save):
                n = self.node('construct', {'type': callee[3], 'new': False, 'args': ', '.join(self.guess(p, a) or 'auto' for a in args)})
                for i, a in enumerate(args): self.feed(a, n.id, f'm{i}')
                return n
            n = self.node('callext', {'name': callee[3], 'ret': (declared or 'auto') if (save or inline) else 'void', 'args': ', '.join(self.guess(p, a) or 'auto' for a in args), **f})
            for i, a in enumerate(args): self.feed(a, n.id, f'm{i}')
            return n
        return None

    def game_call(self, p, c, args, f, declared, _):
        rt = declared if declared and declared != 'auto' and declared != c['r'] else ''
        if not rt and (f.get('save') or f.get('inline')) and c['r'] == 'void': rt = declared or 'auto'  # the catalog says void but the code uses the result: keep the type the code uses
        n = self.node('callgame', {'sym': c['s'], 'rtype': rt, **f})
        for i, a in enumerate(args): self.feed(a, n.id, f'a{i}')
        return n

    # ---- statements ----
    def chain(self, stmts, prev):
        """build statements one after another; prev = (node id, exec pin) to connect from. Returns the last exec pin."""
        for s in stmts:
            if prev is None: break
            n = self.stmt(s)
            if n is None: continue
            self.link(prev[0], prev[1], n.id, 'in')
            prev = (n.id, 'next') if n.type != 'ret' else None
        return prev

    def raw_stmt(self, text): return self.node('stmt', {'tpl': text if text.rstrip().endswith((';', '}')) else text + ';'})

    def declare(self, name, typ): self.types[name] = typ

    def local_node(self, typ, name):
        words = typ.split(); q = []
        while len(words) > 1 and words[0] in ('static', 'constexpr', 'volatile'): q.append(words.pop(0))
        return self.node('local', {'type': ' '.join(words), 'name': name, 'qual': ' '.join(q)} if q else {'type': typ, 'name': name})

    def stmt(self, s):
        p, k = self.p, s[0]
        if k == 'raw': return self.raw_stmt(s[1])
        if k == 'ret':
            n = self.node('ret', {})
            if s[1] is not None: self.feed(s[1], n.id, 'v')
            return n
        if k == 'call':
            c = self.call_node(p, s[1], inline=False)
            return c or self.raw_stmt(p.raw(s[1][1], s[1][2]))
        if k == 'decl':
            _, typ, name, init = s; typ = typ.strip()
            if init is not None and init[0] == 'brace':
                base = re.sub(r'^(?:static|const|constexpr)\s+', '', typ).strip()
                if base == 'auto' or not base: return self.raw_stmt(f'{typ} {name}{p.raw(init[1], init[2])};' if p.t[init[1]].x == '(' else f'{typ} {name} = {p.raw(init[1], init[2])};')
                init = ('brace', init[1], init[2], base, init[4])
            if init is not None and init[0] == 'call':
                c = self.call_node(p, init, inline=False, save=name, declared=typ if typ != 'auto' else '')
                if c and c.type != 'construct': self.declare(name, c.f.get('rtype') or (self.g.sg(c)['r'] if c.type == 'callgame' else c.f.get('ret', typ))); return c
                if c:  # an object built by a constructor: a local variable initialised with it
                    n = self.local_node(typ, name); self.declare(name, typ); self.link(c.id, 'out', n.id, 'v'); return n
            n = self.local_node(typ, name); self.declare(name, typ)
            if init is not None: self.feed(init, n.id, 'v')
            return n
        if k == 'adecl':
            _, typ, name, size, init = s; words = typ.split(); q = []
            while words and words[0] in ('static', 'constexpr', 'volatile'): q.append(words.pop(0))
            n = self.node('local', {'type': ' '.join(words), 'name': name, 'qual': ' '.join(q), 'array': size.strip(), 'ainit': init.strip()}); self.declare(name, ' '.join(words)); return n
        if k == 'assign':
            _, lhs, op, rhs = s
            if op != '=' and op[:-1] in ('+', '-', '*', '/', '%', '&', '|', '^', '<<', '>>') and lhs[0] in ('id', 'member', 'index'):  # x += y  ->  x = x + y
                o = self.node('op', {'op': op[:-1], 'type': self.guess(p, lhs) or self.guess(p, rhs) or 'int'}); self.feed(lhs, o.id, 'a'); self.feed(rhs, o.id, 'b')
                if lhs[0] == 'id': t = self.node('setvar', {'variable': lhs[3]}); self.link(o.id, 'out', t.id, 'v')
                elif lhs[0] == 'member': t = self.node('setmember', {'member': lhs[5], 'arrow': lhs[3]}); self.feed(lhs[4], t.id, 'a'); self.link(o.id, 'out', t.id, 'b')
                else: t = self.node('setindex', {}); self.feed(lhs[3], t.id, 'a'); self.feed(lhs[4], t.id, 'b'); self.link(o.id, 'out', t.id, 'c')
                return t
            if op == '=' and lhs[0] == 'index':
                n = self.node('setindex', {}); self.feed(lhs[3], n.id, 'a'); self.feed(lhs[4], n.id, 'b'); self.feed(rhs, n.id, 'c'); return n
            if lhs[0] == 'id' and (lhs[3] not in self.scope or lhs[3] in self.types):
                n = self.node('setvar', {'variable': lhs[3]})
                if op == '=': self.feed(rhs, n.id, 'v')
                else:
                    o = self.node('op', {'op': op[0], 'type': self.types.get(lhs[3], '') or self.guess(p, rhs) or 'int'}); g = self.node('getvar', {'variable': lhs[3]})
                    self.link(g.id, 'out', o.id, 'a'); self.feed(rhs, o.id, 'b'); self.link(o.id, 'out', n.id, 'v')
                return n
            if op == '=' and lhs[0] == 'member':
                n = self.node('setmember', {'member': lhs[5], 'arrow': lhs[3]}); self.feed(lhs[4], n.id, 'a'); self.feed(rhs, n.id, 'b'); return n
            if op == '=' and lhs[0] == 'deref':
                off = self.offset_pattern(p, lhs[3])
                if off:
                    n = self.node('writeoff', {'type': off[0], 'offset': off[1]}); self.feed(off[2], n.id, 'a'); self.feed(rhs, n.id, 'b'); return n
            return self.raw_stmt(p.raw(lhs[1], rhs[2]))
        if k == 'if':
            n = self.node('if', {}); self.feed(s[1], n.id, 'c'); self.chain_to(n, 'then', s[2])
            if s[3]: self.chain_to(n, 'else', s[3])
            return n
        if k == 'while':
            n = self.node('while', {}); self.feed(s[1], n.id, 'c'); self.chain_to(n, 'body', s[2]); return n
        if k == 'for':
            _, var, (sub, cnt), body = s; n = self.node('for', {'var': var}); old = self.p; self.p = sub; self.feed(cnt, n.id, 'n'); self.p = old
            self.types[var] = 'int'; self.scope[var] = (n.id, 'i'); self.chain_to(n, 'body', body); del self.scope[var]; return n
        if k == 'switch':
            vals = [c[0] for c in s[2] if c[0] != 'default']; n = self.node('switch', {'cases': ', '.join(vals)}); self.feed(s[1], n.id, 'v')
            for lab, body in s[2]: self.chain_to(n, 'c:' + lab, body)
            return n
        return None

    def chain_to(self, n, pin, stmts):
        before = len(self.g.edges); marker = self.node('stmt', {'tpl': ''})  # temporary anchor
        self.chain(stmts, (marker.id, 'next'))
        first = next((e[1] for e in self.g.edges[before:] if e[0] == (marker.id, 'next')), None)
        self.g.edges = [e for e in self.g.edges if e[0][0] != marker.id]; self.g.remove(marker.id); self.ids.remove(marker.id)
        if first: self.link(n.id, pin, first[0], first[1])

    # ---- whole file ----
    def run(self, src):
        g = self.g; items, installs, includes = [], {}, []
        lines = []
        for ln in src.split('\n'):
            if ln.strip().startswith('#'):
                if ln.strip().startswith('#include') and 'lib.hpp' not in ln and 'exlaunch.hpp' not in ln: includes.append(ln.strip())
                lines.append('')
            else: lines.append(ln)
        P = self.p = Parser('\n'.join(lines)); src = P.src; t = P.t; i = 0
        while i < len(t):
            a, d, j = i, 0, i
            while j < len(t):
                x = t[j].x
                if x in OPEN and x != '{': j = P.match(j)
                elif x == '{' and d == 0 and j > a and t[j - 1].x == '=': j = P.match(j)  # int table[3] = {1, 2, 3};  the braces are a value, not a block
                elif x in (';', '{') and d == 0: break
                j += 1
            if j >= len(t): break
            head, term = t[a:j], t[j].x
            hp = next((q for q, h in enumerate(head) if h.x == '('), None)
            if term == '{':
                end = P.match(j)
                if head and head[0].x in ('HOOK_DEFINE_TRAMPOLINE', 'HOOK_DEFINE_REPLACE'): items.append(('hook', head[2].x, j + 1, end, head[0].x == 'HOOK_DEFINE_REPLACE'))
                elif hp is not None and hp > 0:
                    name = head[hp - 1].x; close = P.match(a + hp)
                    ret = ' '.join(h.x for h in head[:hp - 1] if h.x not in QUAL and h.k != 'str' and h.x != 'extern').replace(' ::', '::').replace(':: ', '::').replace(' *', '*').replace(' &', '&').strip()
                    if name == 'exl_main': self.scan_installs(P, j + 1, end, installs)
                    elif name != 'exl_exception_entry': items.append(('func', name, ret or 'void', P.raw(a + hp + 1, close), j + 1, end))
                else: self.report.append(f'Skipped a block that is not a function: {P.raw(a, min(j, a + 4))}...')
                i = end + 1
                if i < len(t) and t[i].x == ';': i += 1
            else:
                if hp is not None and hp >= 2 and term == ';' and head[hp - 1].k == 'id' and P.typelike(a, a + hp - 1) and P.match(a + hp) == j - 1:  # Type name(args);  as a global
                    typ = ' '.join(h.x for h in head[:hp - 1] if h.x not in QUAL).replace(' ::', '::').replace(':: ', '::').replace(' *', '*').replace(' &', '&')
                    items.append(('global', head[hp - 1].x, typ, None, f'{typ}({P.raw(a + hp + 1, j - 1)})', '', '', ''))
                if hp is None and len(head) >= 2:
                    eq = next((q for q, h in enumerate(head) if h.x == '='), len(head)); name = head[eq - 1].x; qual = ' '.join(h.x for h in head if h.x in ('static', 'constexpr', 'volatile') and head.index(h) < eq); arr = ''; ainit = ''
                    qb = next((q for q, h in enumerate(head[:eq]) if h.x == '['), None)
                    if qb is not None:  # Type name[size] = {…};
                        name, arr = head[qb - 1].x, P.raw(a + qb + 1, a + P.match(a + qb) - a); eq0 = qb - 1
                        if eq < len(head) and head[eq + 1].x == '{': ainit = P.raw(a + eq + 2, j - 1)
                        typ = ' '.join(h.x for h in head[:eq0] if h.x not in QUAL).replace(' ::', '::').replace(' *', '*').replace(' &', '&')
                        items.append(('global', name, typ, None, '', qual, arr, ainit)); i = j + 1; continue
                    typ = ' '.join(h.x for h in head[:eq - 1] if h.x not in QUAL).replace(' ::', '::').replace(' *', '*').replace(' &', '&')
                    items.append(('global', name, typ, P.parse_expr(a + eq + 1, j) if eq < len(head) else None, '', qual, '', ''))
                i = j + 1
        # globals first, then function definitions (so calls resolve), then hooks and bodies
        for it in items:
            if it[0] == 'global':
                n = self.node('global', {'type': it[2], 'name': it[1], 'init': P.raw(it[3][1], it[3][2]) if it[3] else it[4], 'qual': it[5], 'array': it[6], 'ainit': it[7]}); self.declare(it[1], it[2])
        groups = []
        for it in items:
            if it[0] == 'func': self.funcs[it[1]] = self.node('func', {'name': it[1], 'ret': it[2], 'params': it[3]})
        for it in items:
            self.ids = []
            if it[0] == 'func':
                fn = self.funcs[it[1]]; self.ids.append(fn.id); self.scope = {}
                for name, typ in parse_params(it[3]): self.scope[name] = (fn.id, name); self.types[name] = typ
                self.chain(self.safe_block(P, it[4], it[5]), (fn.id, 'next')); groups.append((f'Function {it[1]}', list(self.ids)))
            elif it[0] == 'hook': self.hook(P, it, installs, groups)
        self.ids = []
        if includes: g.inc = '\n'.join(includes)
        arrange(g)
        for name, ids in groups: g.make_group(ids, name)
        n = len([1 for x in g.nodes.values() if x.type == 'stmt' and x.f.get('tpl') != ''])
        self.report.insert(0, f'{len(g.nodes)} nodes, {len(g.edges)} links' + (f'; {n} custom statement(s) keep code that could not be turned into blocks' if n else ''))
        return self.report

    def safe_block(self, P, a, b):
        try: return P.block(a, b)
        except ParseError as e: self.report.append(f'Could not parse a function body ({e}); kept as custom code'); return [('raw', P.raw(a, b))] if b > a else []

    def scan_installs(self, P, a, b, out):
        for q in range(a, b - 5):
            if P.t[q].k == 'id' and P.t[q + 1].x == '::' and P.t[q + 3].x == '(':
                if P.t[q + 2].x == 'InstallAtOffset' and P.t[q + 4].k == 'num': out[P.t[q].x] = int(P.t[q + 4].x.rstrip('uUlL'), 0)
                elif P.t[q + 2].x == 'InstallAtSymbol' and P.t[q + 4].x.startswith('"'): out[P.t[q].x] = P.t[q + 4].x.strip('"')

    def hook(self, P, it, installs, groups):
        _, name, a, b = it[:4]; replace_macro = len(it) > 4 and it[4]; q = next((k for k in range(a, b) if P.t[k].x == 'Callback' and P.t[k + 1].x == '('), None)
        if q is None: self.report.append(f'{name}: no Callback function found'); return
        close = P.match(q + 1); params = P.raw(q + 2, close); ret = ' '.join(t.x for t in P.t[a:q] if t.x not in QUAL).strip() or 'void'
        bo = next(k for k in range(close, b) if P.t[k].x == '{'); body = self.safe_block(P, bo + 1, P.match(bo))
        off = installs.get(name); c = (self.g.cat.get(off) if isinstance(off, str) else self.offs.get(off)) if off is not None else None
        if c is None: self.report.append(f'{name}: ' + (f'no catalog function at {off if isinstance(off, str) else hex(off)}' if off is not None else 'no InstallAtOffset / InstallAtSymbol found') + '; the hook keeps an unknown symbol, pick the function by hand (Edit this block)')
        names = [nm for nm, _ in parse_params(params)]
        mode, orig_name = 'replace', None
        n_orig = sum(1 for k in range(bo + 1, P.match(bo)) if P.t[k].x == 'Orig' and P.t[k + 1].x == '(')
        self.hook_args = names; self.hook_ret = ret
        def is_orig(s): return s[0] == 'call' and s[1][3][0] == 'id' and s[1][3][3] == 'Orig'
        if replace_macro: pass  # HOOK_DEFINE_REPLACE has no Orig
        elif n_orig == 1 and body and is_orig(body[0]): mode = 'before'; body = body[1:]
        elif n_orig == 1 and body and body[0][0] == 'decl' and body[0][3] and body[0][3][0] == 'call' and body[0][3][3][0] == 'id' and body[0][3][3][3] == 'Orig': mode, orig_name = 'before', body[0][2]; body = body[1:]
        elif n_orig == 1 and body and ((body[-1][0] == 'ret' and body[-1][1] and body[-1][1][0] == 'call' and body[-1][1][3][0] == 'id' and body[-1][1][3][3] == 'Orig') or is_orig(body[-1])): mode = 'after'; body = body[:-1]
        if n_orig and mode == 'replace' and not replace_macro: mode = 'manual'  # Orig somewhere else: "Call original" blocks keep its position
        if mode == 'before' and body and body[-1][0] == 'ret' and body[-1][1] and body[-1][1][0] == 'id' and body[-1][1][3] == (orig_name or 'orig_ret'): body = body[:-1]
        if mode == 'replace' and body and body[-1][0] == 'ret' and body[-1][2].replace(' ', '') == 'return{};': body = body[:-1]
        h = self.node('hook', {'sym': c['s'] if c else (off if isinstance(off, str) else f'?0x{off or 0:x}'), 'mode': mode, 'ret': ret if c and ret != c['r'] else '', 'names': ', '.join(names) if names != [f'p{i}' for i in range(len(names))] else ''})
        self.scope = {nm: (h.id, f'p{i}') for i, nm in enumerate(names)}; self.types = {k: v for k, v in self.types.items() if k not in self.scope}
        for i, (nm, ty) in enumerate(parse_params(params)): self.types[nm] = ty
        if mode == 'before': self.scope[orig_name or 'orig_ret'] = (h.id, 'orig')
        self.ids.append(h.id); self.chain(body, (h.id, 'next')); groups.append((f'Hook {c["n"] if c else name}', list(self.ids)))


def import_cpp(src, catalog_graph):
    """-> (new Graph with the same catalog, report lines)"""
    g = Graph(); g.cat, g.overrides = catalog_graph.cat, catalog_graph.overrides
    rep = Importer(g).run(src); return g, rep
