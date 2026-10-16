# SPDX-License-Identifier: CC0-1.0
"""Track/via/pad connectivity of Eagle signals without polygon pours."""
import math, sys
from collections import defaultdict
sys.path.insert(0, '.')
import eagle_model

def in_pad(B, p, pt, extra=0.0):
    kind, w, h, a = B.pad_geometry(p)
    dx, dy = pt[0]-p['pos'][0], pt[1]-p['pos'][1]
    ra = math.radians(-a); lx = dx*math.cos(ra)-dy*math.sin(ra); ly = dx*math.sin(ra)+dy*math.cos(ra)
    if kind == 'circle': return math.hypot(lx, ly) <= w/2 + extra + 1e-4
    if kind == 'oval':
        r = h/2; hx = max(abs(lx) - (w/2 - r), 0); return math.hypot(hx, ly) <= r + extra + 1e-4
    return abs(lx) <= w/2 + extra + 1e-4 and abs(ly) <= h/2 + extra + 1e-4

def islands(B, net, use_airwires=False):
    items = []
    pads = [p for p in B.pads if p['signal'] == net]
    smds = [s for s in B.smds if s['signal'] == net]
    wires = [w for w in B.wires if w['signal'] == net and (w['layer'] in (1, 16) or (use_airwires and w['layer'] == 19))]
    vias = [v for v in B.vias if v['signal'] == net]
    n = len(pads)+len(smds)+len(wires)+len(vias)
    par = list(range(n))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    def u(a, b): par[f(a)] = f(b)
    off_s = len(pads); off_w = off_s+len(smds); off_v = off_w+len(wires)
    ends = defaultdict(list)
    for i, w in enumerate(wires):
        for pt in (w['p1'], w['p2']):
            ends[(round(pt[0], 3), round(pt[1], 3))].append(off_w+i)
    for k, lst in ends.items():
        for j in lst[1:]: u(lst[0], j)
    def segd(w, q):
        (x1, y1), (x2, y2) = w['p1'], w['p2']
        dx, dy = x2-x1, y2-y1; L = dx*dx+dy*dy
        t_ = 0 if L == 0 else max(0, min(1, ((q[0]-x1)*dx+(q[1]-y1)*dy)/L))
        return math.hypot(x1+t_*dx-q[0], y1+t_*dy-q[1])
    for i, w in enumerate(wires):
        if w['layer'] in (1, 16) and not w['curve']:
            for j, p in enumerate(pads):
                if segd(w, p['pos']) <= w['width']/2: u(off_w+i, j)
            for j, v in enumerate(vias):
                if segd(w, v['pos']) <= w['width']/2: u(off_w+i, off_v+j)
    for i, w in enumerate(wires):
        for pt in (w['p1'], w['p2']):
            for j, p in enumerate(pads):
                if in_pad(B, p, pt, w['width']/2 if w['layer'] != 19 else 0): u(off_w+i, j)
            for j, s in enumerate(smds):
                if (w['layer'] == s['layer'] or w['layer'] == 19) and abs(pt[0]-s['pos'][0]) <= max(s['dx'], s['dy'])/2 and abs(pt[1]-s['pos'][1]) <= max(s['dx'], s['dy'])/2: u(off_w+i, off_s+j)
            for j, v in enumerate(vias):
                if math.hypot(pt[0]-v['pos'][0], pt[1]-v['pos'][1]) < 0.01: u(off_w+i, off_v+j)
    groups = defaultdict(list)
    names = [f"{p['element']}.{p['name']}" for p in pads]+[f"{s['element']}.{s['name']}" for s in smds]+['wire']*len(wires)+['via']*len(vias)
    for i in range(n): groups[f(i)].append(names[i])
    return sorted(groups.values(), key=len, reverse=True)

if __name__ == '__main__':
    from compare import EAGLE as E
    for b, nets in (('mainboard', ['GND', '+5V']), ('ioboard', ['GND'])):
        B = eagle_model.Board(E+b+'.brd')
        for net in nets:
            for aw in (False, True):
                g = islands(B, net, aw)
                print(b, net, 'with stored airwires' if aw else 'tracks only', 'islands', len(g), [len(x) for x in g][:12], 'pad-only islands:', [x for x in g if all(n != 'wire' and n != 'via' for n in x)][:20])
