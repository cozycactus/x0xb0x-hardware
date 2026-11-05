"""Extract per-reference footprint geometry from the x0xb0x KiCad boards.

Reads the boards read-only and writes work/footprints.json: reference,
value, footprint name, pad count, minimum pad pitch, pad span, drill sizes
and fab/silk/courtyard outline extents in footprint coordinates (mm).
Run from the repository root:
  python3 -I parts/scripts/extract_footprints.py kicad-working/mainboard/mainboard.kicad_pcb kicad-working/ioboard/ioboard.kicad_pcb
"""
import json, math, re, sys
from pathlib import Path

def tokenize(s):
    for m in re.finditer(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s):
        yield m.group(0)

def parse(s):
    stack = [[]]
    for t in tokenize(s):
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t[1:-1] if t.startswith('"') else t)
    return stack[0][0]

def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]

def first(node, key):
    r = find(node, key); return r[0] if r else None

def geom_points(item):
    pts = []
    for k in ('start', 'end', 'center', 'mid'):
        p = first(item, k)
        if p: pts.append((float(p[1]), float(p[2])))
    if item[0] == 'fp_circle' and first(item, 'center') and first(item, 'end'):
        c = first(item, 'center'); e = first(item, 'end')
        cx, cy = float(c[1]), float(c[2]); r = math.dist((cx, cy), (float(e[1]), float(e[2])))
        pts += [(cx - r, cy - r), (cx + r, cy + r)]
    pl = first(item, 'pts')
    if pl:
        pts += [(float(x[1]), float(x[2])) for x in find(pl, 'xy')]
    return pts

def ext(pts):
    if not pts: return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3)

out = []
for board in sys.argv[1:]:
    tree = parse(Path(board).read_text())
    for fp in find(tree, 'footprint'):
        props = {p[1]: p[2] for p in find(fp, 'property')}
        ref = props.get('Reference'); val = props.get('Value')
        for t in find(fp, 'fp_text'):
            if t[1] == 'reference': ref = t[2]
            if t[1] == 'value': val = t[2]
        pads = []
        for p in find(fp, 'pad'):
            at = first(p, 'at'); size = first(p, 'size'); drill = first(p, 'drill')
            d = None
            if drill:
                nums = [x for x in drill[1:] if not isinstance(x, list) and x != 'oval']
                d = '/'.join(nums)
            pads.append({'name': p[1], 'type': p[2], 'x': float(at[1]), 'y': float(at[2]),
                         'size': [float(size[1]), float(size[2])], 'drill': d})
        layers = {}
        for kind in ('fp_line', 'fp_rect', 'fp_circle', 'fp_arc', 'fp_poly'):
            for g in find(fp, kind):
                lay = first(g, 'layer')
                if lay: layers.setdefault(lay[1], []).extend(geom_points(g))
        pitch = None
        pos = sorted({(round(p['x'], 3), round(p['y'], 3)) for p in pads})
        if len(pos) > 1:
            pitch = round(min(math.dist(a, b) for i, a in enumerate(pos) for b in pos[i+1:]), 3)
        out.append({
            'board': Path(board).stem, 'ref': ref, 'value': val, 'footprint': fp[1],
            'pads': len(pads), 'min_pitch_mm': pitch,
            'pad_span_mm': ext([(p['x'], p['y']) for p in pads]),
            'drills_mm': sorted({p['drill'] for p in pads if p['drill']}),
            'fab_extent_mm': ext(layers.get('F.Fab', []) or layers.get('B.Fab', [])),
            'silk_extent_mm': ext(layers.get('F.SilkS', []) or layers.get('B.SilkS', [])),
            'courtyard_extent_mm': ext(layers.get('F.CrtYd', []) or layers.get('B.CrtYd', [])),
            'pad_coords': [(p['name'], p['x'], p['y']) for p in pads],
        })
json.dump(out, open(Path(__file__).resolve().parent.parent / 'work' / 'footprints.json', 'w'), indent=1)
print(len(out))
