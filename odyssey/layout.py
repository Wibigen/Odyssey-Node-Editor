"""Automatic node arrangement (used after a C++ import, a library insert, or Edit > Arrange)."""
from .graph import E

COLW, NODE_W, PAD = 340, 270, 22


def node_h(g, n):
    t, ins, outs = g.spec(n)
    return 36 + (20 if g.subtitle(n) else 0) + 22 * max(len(ins), len(outs), 1) + 8


def arrange(g, ids=None):
    """Return {node id: (x, y)} starting at (0, 0). Execution chains run left to right, branches stack downward,
    value nodes sit under the node that uses them."""
    ids = set(g.nodes) if ids is None else {i for i in ids if i in g.nodes}
    placed, pos, H = [], {}, {i: node_h(g, g.nodes[i]) for i in ids}

    def put(nid, x, y):
        if nid in pos or nid not in ids: return
        w, h, moved = NODE_W, H[nid], True
        while moved:
            moved = False
            for px, py, pw, ph in placed:
                if x < px + pw + PAD and px < x + w + PAD and y < py + ph + PAD and py < y + h + PAD: y = py + ph + PAD; moved = True
        placed.append((x, y, w, h)); pos[nid] = (x, y)

    def is_exec(nid): return any(p.type == E for p in g.spec(g.nodes[nid])[1])

    def data_deps(nid):
        return [e[0][0] for e in g.edges if e[1][0] == nid and g.pin_type(e[1][0], e[1][1], 'i') != E and e[0][0] in ids]

    def place_data(nid):
        x, y = pos[nid]; cy = y + H[nid] + PAD
        for d in data_deps(nid):
            if d in pos or is_exec(d) or g.nodes[d].type in ('hook', 'func'): continue
            put(d, x, cy); cy = pos[d][1] + H[d] + PAD; place_data(d)

    def walk(nid, x, y):
        xmax = x
        while nid and nid in ids and nid not in pos:
            put(nid, x, y); place_data(nid); x0, y0 = pos[nid]; xmax = max(xmax, x)
            for p in g.spec(g.nodes[nid])[2]:
                if p.type == E and p.id != 'next':
                    t = g.nxt(nid, p.id)
                    if t: xmax = max(xmax, walk(t, x + COLW, y0))
            nid = g.nxt(nid, 'next'); x = xmax + COLW if xmax > x else x + COLW
        return xmax

    y = 0
    for r in sorted(i for i in ids if g.nodes[i].type in ('hook', 'func')):
        if r in pos: continue
        put(r, 0, y); walk(g.nxt(r, 'next'), COLW, pos[r][1]); y = max([py + ph for (px, py, pw, ph) in placed] + [y]) + 70
    for i in sorted(ids):  # whatever is left: globals, loose nodes
        if i not in pos: put(i, 0, y); place_data(i); y = max(y, pos[i][1] + H[i] + PAD)
    return pos


def apply(g, ids=None, dx=0.0, dy=0.0):
    for i, (x, y) in arrange(g, ids).items(): g.nodes[i].x, g.nodes[i].y = x + dx, y + dy
